from flask import Flask, render_template, request, redirect, jsonify, flash, url_for
from parsers.syllabus_parser import parse_syllabus_pdf
from db.connection import get_db_connection
import os

app = Flask(__name__)
# REQUIRED: Add a secret key for flash messages to work
app.secret_key = "your-random-secret-key-123!" # Changed this for you
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    db = None
    cursor = None
    courses = [] # Default to an empty list
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True) # Use dictionary=True to access columns by name
        
        # --- NEW SQL QUERY ---
        # Calculates the average completion percentage for each course
        sql = """
            SELECT
                C.course_id,
                C.COURSE_NAME,
                C.course_code,
                COALESCE(AVG(T.completion_status), 0) AS completion_percentage
            FROM
                Course C
            LEFT JOIN
                Module M ON C.course_id = M.course_id
            LEFT JOIN
                Topics T ON M.module_id = T.module_id
            GROUP BY
                C.course_id, C.COURSE_NAME, C.course_code
            ORDER BY
                C.COURSE_NAME;
        """
        cursor.execute(sql)
        courses = cursor.fetchall()
        
    except Exception as e:
        print(f"Error fetching courses: {e}") # Log the error
        flash(f"Database Error: Could not fetch courses. {e}", "error")
    finally:
        if cursor: cursor.close()
        if db: db.close()
        
    # Pass the list of courses (which now includes 'completion_percentage')
    return render_template("upload.html", courses=courses)

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if 'file' not in request.files:
        flash("No file part in request.", "error")
        return redirect(url_for('home'))
        
    file = request.files['file']
    if file.filename == '':
        flash("No file selected for upload.", "error")
        return redirect(url_for('home'))

    if file:
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        
        course_id = None # Initialize
        try:
            course_id = parse_syllabus_pdf(path)
        except Exception as e:
            print(f"CRITICAL PARSER ERROR: {e}")
            flash(f"A critical error occurred during parsing: {e}", "error")
            return redirect(url_for('home'))

        if course_id:
            flash("Syllabus uploaded and parsed successfully!", "success")
            return redirect(url_for('dashboard', course_id=course_id))
        else:
            flash("Failed to parse the PDF. Please check the file and try again.", "error")
            return redirect(url_for('home'))

@app.route("/dashboard/<int:course_id>")
def dashboard(course_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    course = None
    module_data = []

    try:
        cursor.execute("SELECT * FROM Course WHERE course_id = %s", (course_id,))
        course = cursor.fetchone()

        if not course:
             flash(f"No course found with ID {course_id}.", "error")
             return redirect(url_for('home'))

        cursor.execute("SELECT * FROM Module WHERE course_id = %s ORDER BY module_id", (course_id,))
        modules = cursor.fetchall()

        for m in modules:
            cursor.execute("SELECT * FROM Topics WHERE module_id = %s ORDER BY topic_id", (m['module_id'],))
            topics = cursor.fetchall()
            module_data.append({"module": m, "topics": topics})
            
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard data: {e}", "error")
        return redirect(url_for('home'))
    finally:
        cursor.close()
        db.close()
        
    return render_template("dashboard.html", course=course, module_data=module_data)

# --- NEW ROUTE FOR ADDING A CUSTOM COURSE ---

@app.route('/add_course', methods=['POST'])
def add_course():
    """
    Creates a new, blank course from the form on the home page.
    """
    db = None
    cursor = None
    try:
        course_name = request.form.get('course_name')
        course_code = request.form.get('course_code')

        if not course_name or not course_code:
            flash("Course name and code are required.", "error")
            return redirect(url_for('home'))

        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "INSERT INTO Course (COURSE_NAME, course_code) VALUES (%s, %s)",
            (course_name, course_code)
        )
        course_id = cursor.lastrowid # Get the ID of the new course
        db.commit()
        
        flash(f"New course '{course_name}' created! Add modules and topics.", "success")
        # Redirect the user straight to the dashboard for their new course
        return redirect(url_for('dashboard', course_id=course_id))

    except Exception as e:
        if db: db.rollback()
        print(f"Error creating course: {e}")
        flash(f"Error creating course: {e}", "error")
        return redirect(url_for('home'))
    finally:
        if cursor: cursor.close()
        if db: db.close()

# --- COURSE MANAGEMENT ROUTES (CALLED FROM HOME) ---

@app.route('/update_course/<int:course_id>', methods=['POST'])
def update_course(course_id):
    """
    Updates the course name and code from the home page.
    """
    db = None
    cursor = None
    try:
        new_name = request.form.get('course_name')
        new_code = request.form.get('course_code')
        
        if not new_name or not new_code:
            flash("Course name and code cannot be empty.", "error")
            return redirect(url_for('home')) # Redirect to home

        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "UPDATE Course SET COURSE_NAME = %s, course_code = %s WHERE course_id = %s",
            (new_name, new_code, course_id)
        )
        db.commit()
        flash("Course details updated successfully!", "success")
        
    except Exception as e:
        if db: db.rollback()
        print(f"Error updating course: {e}")
        flash(f"Error updating course: {e}", "error")
    finally:
        if cursor: cursor.close()
        if db: db.close()
        
    # Redirect back to the home page to see the change
    return redirect(url_for('home'))

@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    """
    Deletes a course from the home page.
    """
    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "DELETE FROM Course WHERE course_id = %s",
            (course_id,)
        )
        db.commit()
        flash(f"Course successfully deleted.", "success")
        
    except Exception as e:
        if db: db.rollback()
        print(f"Error deleting course: {e}")
        flash(f"Error deleting course: {e}", "error")
    finally:
        if cursor: cursor.close()
        if db: db.close()

    # After deleting, send the user back to the home page
    return redirect(url_for('home'))

# --- MODULE & TOPIC ROUTES (CALLED FROM DASHBOARD) ---

@app.route("/update_topic_stats/<int:topic_id>", methods=["POST"])
def update_topic_stats(topic_id):
    completion = request.form.get("completion")
    importance = request.form.get("importance")
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE Topics SET completion_status=%s, importance=%s WHERE topic_id=%s",
                       (completion, importance, topic_id))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()
        
    return jsonify({"message": "Updated successfully!"})

@app.route('/update_module/<int:module_id>', methods=['POST'])
def update_module(module_id):
    db = None
    cursor = None
    try:
        new_name = request.form.get('module_name')
        new_hours = request.form.get('module_hours')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "UPDATE Module SET module_name = %s, module_hours = %s WHERE module_id = %s",
            (new_name, new_hours, module_id)
        )
        db.commit()
        return jsonify({"success": True, "message": "Module updated"}), 200
    except Exception as e:
        if db: db.rollback()
        print(f"Error updating module: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if db: db.close()

@app.route('/rename_topic/<int:topic_id>', methods=['POST'])
def rename_topic(topic_id):
    db = None
    cursor = None
    try:
        new_name = request.form.get('topic_name')
        if not new_name:
            return jsonify({"error": "Topic name cannot be empty"}), 400

        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "UPDATE Topics SET topic_name = %s WHERE topic_id = %s",
            (new_name, topic_id)
        )
        db.commit()
        return jsonify({"success": True, "message": "Topic renamed"}), 200
    except Exception as e:
        if db: db.rollback()
        print(f"Error renaming topic: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if db: db.close()

@app.route('/delete_topic/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "DELETE FROM Topics WHERE topic_id = %s",
            (topic_id,)
        )
        db.commit()
        return jsonify({"success": True, "message": "Topic deleted"}), 200
    except Exception as e:
        if db: db.rollback()
        print(f"Error deleting topic: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if db: db.close()

@app.route('/add_topic/<int:module_id>', methods=['POST'])
def add_topic(module_id):
    db = None
    cursor = None
    try:
        topic_name = request.form.get('topic_name')
        if not topic_name:
            return jsonify({"error": "Topic name cannot be empty"}), 400

        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "INSERT INTO Topics (module_id, topic_name, completion_status, importance) VALUES (%s, %s, 0, 0)",
            (module_id, topic_name)
        )
        db.commit()
        return jsonify({"success": True, "message": "Topic added"}), 201
    except Exception as e:
        if db: db.rollback()
        print(f"Error adding topic: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if db: db.close()
# In app.py

@app.route('/add_module/<int:course_id>', methods=['POST'])
def add_module(course_id):
    """Adds a new, empty module to a course."""
    db = None
    cursor = None
    try:
        module_name = request.form.get('module_name')
        module_hours = request.form.get('module_hours', 0) # Default to 0 hours

        if not module_name:
            flash("Module name cannot be empty.", "error")
            return redirect(url_for('dashboard', course_id=course_id))

        # --- Determine the next module number ---
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT MAX(module_number) as max_num FROM Module WHERE course_id = %s", (course_id,))
        result = cursor.fetchone()
        next_module_number = (result['max_num'] or 0) + 1
        
        # Reopen cursor without dictionary=True for insert
        cursor.close() 
        cursor = db.cursor() 
        
        # --- Insert the new module ---
        cursor.execute(
            "INSERT INTO Module (course_id, module_number, Module_name, Module_hours) VALUES (%s, %s, %s, %s)",
            (course_id, next_module_number, module_name, module_hours)
        )
        db.commit()
        flash("New module added successfully!", "success")
        
    except Exception as e:
        if db: db.rollback()
        print(f"Error adding module: {e}")
        flash(f"Error adding module: {e}", "error")
    finally:
        if cursor: cursor.close()
        if db: db.close()
        
    return redirect(url_for('dashboard', course_id=course_id))

@app.route('/delete_module/<int:module_id>', methods=['POST'])
def delete_module(module_id):
    """Deletes a module and its topics (due to CASCADE)."""
    db = None
    cursor = None
    course_id = None # Need course_id to redirect back
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True) # Use dictionary for SELECT

        # --- Get course_id before deleting for redirection ---
        cursor.execute("SELECT course_id FROM Module WHERE module_id = %s", (module_id,))
        module = cursor.fetchone()
        if module:
            course_id = module['course_id']
        else:
            flash("Module not found.", "error")
            return redirect(url_for('home')) # Or some error page

        # Reopen cursor without dictionary=True for delete
        cursor.close()
        cursor = db.cursor()

        # --- Delete the module (CASCADE handles topics) ---
        cursor.execute("DELETE FROM Module WHERE module_id = %s", (module_id,))
        db.commit()
        flash("Module deleted successfully!", "success")
        
    except Exception as e:
        if db: db.rollback()
        print(f"Error deleting module: {e}")
        flash(f"Error deleting module: {e}", "error")
    finally:
        if cursor: cursor.close()
        if db: db.close()

    # Redirect back to the dashboard if possible, otherwise home
    if course_id:
        return redirect(url_for('dashboard', course_id=course_id))
    else:
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)