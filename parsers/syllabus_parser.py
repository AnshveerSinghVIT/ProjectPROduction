import pdfplumber
import re
import os
from db.connection import get_db_connection

def parse_syllabus_pdf(pdf_path):
    db = get_db_connection()
    cursor = db.cursor()

    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    # Course name/code
    match = re.search(r"([A-Z0-9]+)\s+([A-Za-z\s]+)\s+\d\s\d\s\d\s\d", full_text)
    if match:
        course_code = match.group(1).strip()
        course_name = match.group(2).strip()
    else:
        course_name, course_code = "Unknown Course", "Unknown Code"

    cursor.execute("INSERT INTO Course (course_name, course_code) VALUES (%s, %s)", (course_name, course_code))
    course_id = cursor.lastrowid

    module_pattern = re.compile(
        r"(Module:(\d+)\s*(.*?)\s*(\d+)\s*hours)([\s\S]*?)(?=(Module:\d+)|(Total Lecture hours:))",
        re.DOTALL
    )

    for m in module_pattern.finditer(full_text):
        _, mod_num, mod_name, mod_hours, topics_text, _, _ = m.groups()
        module_name = f"Module:{mod_num} {mod_name.strip()}"
        cursor.execute("INSERT INTO Module (course_id, module_number, module_name, module_hours) VALUES (%s, %s, %s, %s)",
                       (course_id, int(mod_num), module_name, int(mod_hours)))
        module_id = cursor.lastrowid

        topics = topics_text.strip().split(' - ')
        for t in topics:
            t = t.replace('\n', ' ').strip()
            if t:
                cursor.execute("INSERT INTO Topics (module_id, topic_name) VALUES (%s, %s)", (module_id, t))

    db.commit()
    cursor.close()
    db.close()
    return course_id
