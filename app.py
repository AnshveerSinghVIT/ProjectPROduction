from flask import Flask, render_template, request, redirect, jsonify
from parsers.syllabus_parser import parse_syllabus_pdf
from db.connection import get_db_connection
import os

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files['file']
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    course_id = parse_syllabus_pdf(path)
    return redirect(f"/dashboard/{course_id}")

@app.route("/dashboard/<int:course_id>")
def dashboard(course_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Course WHERE course_id = %s", (course_id,))
    course = cursor.fetchone()

    cursor.execute("SELECT * FROM Module WHERE course_id = %s", (course_id,))
    modules = cursor.fetchall()

    module_data = []
    for m in modules:
        cursor.execute("SELECT * FROM Topics WHERE module_id = %s", (m['module_id'],))
        topics = cursor.fetchall()
        module_data.append({"module": m, "topics": topics})

    cursor.close()
    db.close()
    return render_template("dashboard.html", course=course, module_data=module_data)

@app.route("/update_topic/<int:topic_id>", methods=["POST"])
def update_topic(topic_id):
    completion = request.form.get("completion")
    importance = request.form.get("importance")
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE Topics SET completion_status=%s, importance=%s WHERE topic_id=%s",
                   (completion, importance, topic_id))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"message": "Updated successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
