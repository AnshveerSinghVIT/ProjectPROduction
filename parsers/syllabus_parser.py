import pdfplumber
import sys
import re
import os
from db.connection import get_db_connection  # Your database connection

def get_full_table(doc):
    """
    Extracts tables from all pages and combines them into one list.
    """
    all_rows = []
    print(f"--- Processing {len(doc.pages)} pages ---")

    for i, page in enumerate(doc.pages):
        # extract_tables() is safer as it always returns a list
        tables = page.extract_tables()
        print(f"\n--- Page {i + 1}: Found {len(tables)} table(s) ---")

        if tables:
            # Assume we want the first table on the page
            table_part = tables[0]
            all_rows.extend(table_part)
            print(f"Added {len(table_part)} rows from this page.")
            
    return all_rows

# --- THIS IS THE FUNCTION YOUR FLASK APP CALLS ---
def parse_syllabus_pdf(file_path):
    """
    Runs the full table-parsing pipeline and inserts
    the data into the database according to the provided schema.
    
    Called by the Flask /upload route.
    """
    db = None
    cursor = None
    course_id = None # Initialize course_id
    
    try:
        # --- 1. Database Setup ---
        db = get_db_connection()
        cursor = db.cursor()
        print("Database connection successful.")

        # --- 2. Robust Table Parsing ---
        with pdfplumber.open(file_path) as pdf:
            
            full_table = get_full_table(pdf)
            
            if not full_table:
                print("No table data found in the entire document.")
                return None # Return None if parsing fails

            # --- 3. Parse Course Info (from stable table row) ---
            first_row = full_table[0]
            cleaned_first_row = [cell for cell in first_row 
                                 if cell is not None and cell.strip() != '']
            
            course_code = cleaned_first_row[0] if len(cleaned_first_row) > 0 else "Unknown Code"
            course_name = cleaned_first_row[1] if len(cleaned_first_row) > 1 else "Unknown Name"
            
            print(f"\nProcessing: {course_code}: {course_name}")

            # --- 4. DB Insert: Course (Matches your schema) ---
            cursor.execute("INSERT INTO Course (course_code, COURSE_NAME) VALUES (%s, %s)", 
                           (course_code, course_name))
            course_id = cursor.lastrowid
            print(f"Inserted Course with ID: {course_id}")

            # --- 5. Merge Module Rows ---
            content_rows = full_table[10:25] # Your specified slice
            merged_rows = []
            for row in content_rows:
                cleaned_row = [cell for cell in row 
                               if cell is not None and cell.strip() != '']
                if not cleaned_row:
                    continue
                if cleaned_row[0].startswith('Module:'):
                    merged_rows.append(cleaned_row)
                else:
                    if not merged_rows or merged_rows[-1][0].startswith('Module:'):
                        merged_rows.append(cleaned_row)
                    else:
                        continuation_text = " " + cleaned_row[0]
                        merged_rows[-1][0] += continuation_text

            # --- 6. Parse Topics & Insert Modules/Topics ---
            i = 0
            while i < len(merged_rows):
                row = merged_rows[i]
                
                if row[0].startswith('Module:'):
                    # --- FIXED: Robust RegEx matching ---
                    
                    # 1. Safely parse Module Number
                    mod_num_match = re.search(r'Module:(\d+)', row[0])
                    if not mod_num_match:
                        # Handle failure: Maybe log it or use a default
                        print(f"Warning: Could not parse module number from '{row[0]}'. Using 0.")
                        mod_num_str = "0"
                    else:
                        mod_num_str = mod_num_match.group(1)

                    mod_num = int(mod_num_str) if mod_num_str.isdigit() else 0
                    mod_name = row[1] # Assumes row[1] is always the name

                    # 2. Safely parse Module Hours (from row[2])
                    mod_hours_match = re.search(r'(\d+)', row[2]) # Made regex simpler
                    if not mod_hours_match:
                        # Handle failure: Use 0 if no number is found
                        print(f"Warning: Could not parse hours from '{row[2]}'. Using 0.")
                        mod_hours_str = "0"
                    else:
                        mod_hours_str = mod_hours_match.group(1)

                    mod_hours = int(mod_hours_str) if mod_hours_str.isdigit() else 0
                    # --- END OF FIX ---
                    
                    full_module_name = f"Module:{mod_num} {mod_name}"

                    # --- DB Insert: Module (Matches your schema) ---
                    cursor.execute("INSERT INTO Module (course_id, module_number, Module_name, Module_hours) VALUES (%s, %s, %s, %s)",
                                (course_id, mod_num, full_module_name, mod_hours))
                    module_id = cursor.lastrowid

                    # Check for description row
                    if (i + 1) < len(merged_rows) and not merged_rows[i+1][0].startswith('Module:'):
                        desc_string = merged_rows[i+1][0].replace('\n', ' ')
                        
                        # --- Smart Delimiter Logic ---
                        comma_count = desc_string.count(',')
                        dash_count = desc_string.count('-') + desc_string.count('–')
                        
                        topics_list = []
                        if dash_count > comma_count:
                            topics_list = [t.strip() for t in re.split(r'\s*-\s*|\s*–\s*', desc_string) if t.strip()]
                        else:
                            topics_list = [t.strip() for t in desc_string.split(',') if t.strip()]
                        
                        # --- DB Insert: Topics (Matches your schema) ---
                        # --- DB Insert: Topics (Matches your schema image) ---
                        default_importance = 0
                        default_status = 0
                        for topic in topics_list:
                            # Wrap "completion status" in backticks
                            cursor.execute(
                                "INSERT INTO Topics (module_id, topic_name, importance, completion_status) VALUES (%s, %s, %s, %s)", 
                                (module_id, topic, default_importance, default_status)
                            )
                        
                        i += 2 # Move past both header and description
                    else:
                        i += 1 # No topics, just skip header
                else:
                    i += 1 # Safeguard
            
            # --- 7. Finalize Transaction ---
            db.commit()
            print(f"\n--- SUCCESS! ---")
            print(f"Syllabus data for {course_code} saved to database.")
            
            # --- Return the course_id to Flask ---
            return course_id

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        if db:
            print("Rolling back database changes.")
            db.rollback()
        return None # Return None on error
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
            print("Database connection closed.")