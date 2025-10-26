# ProjectPROduction: Automated Syllabus Tracker

A smart web application designed to automatically parse course syllabi from PDF files (like those from VIT) and turn them into an interactive progress tracker. You can also create and manage fully custom courses from scratch.

![ProjectPROduction Demo](https://via.placeholder.com/720x400.png?text=Add+a+GIF+or+Screenshot+of+your+App!)
*(Recommendation: Record a short GIF of your app working—especially the PDF upload—and replace the link above!)*

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [How the PDF Parsing Works](#how-the-pdf-parsing-works)
- [Technologies Used](#technologies-used)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Manually typing out an entire syllabus into a to-do list is tedious. **ProjectPROduction** solves this by automating the most difficult part.

This tool provides two main pathways for students:

1.  **Automated PDF Parsing:** Upload your course syllabus (e.g., from VIT). The application uses `pdfplumber` to read the PDF, extract all the modules, topics, and sub-topics, and automatically populate the database, creating a full course structure in seconds.
2.  **Custom Course Creation:** If you don't have a PDF or are self-studying, you can use the simple UI to build your own course, add modules, and list topics manually.

Once a course is created, you can track the status of each topic ("Completed," "In Progress," or "Not Started") and see your overall progress with a visual progress bar.

## Key Features

* ✨ **Smart PDF Parsing:** Automatically builds a course structure by reading and interpreting syllabus PDF files.
* 🎓 **Optimized for VIT:** The parsing logic is tailored to understand the common structure of VIT (Vellore Institute ofTechnology) syllabi.
* 📝 **Custom Course Builder:** A full-featured editor to create and structure your own courses, modules, and topics from scratch.
* 📊 **Visual Progress Tracking:** A clean dashboard shows your completion percentage for each course.
* 💾 **Persistent Storage:** All courses and progress are saved to a reliable **MySQL** database.
* 📱 **Responsive UI:** A clean and simple interface that works on both desktop and mobile.

---

## How the PDF Parsing Works

The core of this project is its ability to parse unstructured PDF data. Here’s a simple breakdown of the process:

1.  **Upload:** The user uploads a syllabus PDF file through the web interface.
2.  **Extract:** The backend uses the `pdfplumber` library to open the PDF and extract all text content, page by page.
3.  **Analyze & Structure:** Custom Python logic (your "secret sauce") iterates through the extracted text. It searches for keywords (like "Module:", "Unit-", "Topic:", etc.) to identify the course structure.
4.  **Populate:** Once the modules and their respective topics are identified, the application automatically inserts them into the MySQL database, linking them to the user and the new course.
5.  **Done!** The user is redirected to their new course, which is now fully built and ready to be tracked, all without typing a single topic.

---

## Technologies Used

* **Backend:** Python
* **Web Framework:** [Specify your framework, e.g., Flask, Django, Streamlit]
* **PDF Parsing:** `pdfplumber`
* **Database:** MySQL
* **Database Connector:** `mysql-connector-python`
* **Frontend:** HTML, CSS, JavaScript [Specify any frameworks, e.g., React, Bootstrap]

---

## Setup and Installation

To get a local copy up and running, follow these steps.

**Prerequisites:**

* Python 3.x
* `pip` (Python package installer)
* A running **MySQL Server** instance

**Installation Steps:**

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/AnshveerSinghVIT/ProjectPROduction.git](https://github.com/AnshveerSinghVIT/ProjectPROduction.git)
    cd ProjectPROduction
    ```

2.  **Create and activate a virtual environment (Recommended):**
    ```sh
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    *(Create a `requirements.txt` file first: `pip freeze > requirements.txt`)*
    ```sh
    pip install -r requirements.txt
    ```
    *(Or, install manually)*
    ```sh
    pip install pdfplumber mysql-connector-python [your-web-framework-e.g.-flask]
    ```

4.  **Configure the Database:**
    * Access your MySQL server and create a new database:
        ```sql
        CREATE DATABASE projectpro_db;
        ```
    * Find the application's configuration file (e.g., `config.py`, `.env`, or directly in `app.py`).
    * Update the database connection settings with your MySQL username, password, and the database name (`projectpro_db`).

5.  **Initialize the Database:**
    * [Explain how to create your tables. e.g., if you have an `init_db.py` script or are using an ORM like SQLAlchemy]
    * *Example:* `python init_db.py`
    * *Example (Flask-SQLAlchemy):* `flask db upgrade`

6.  **Run the application:**
    ```sh
    python app.py
    ```
    Or (if using Flask):
    ```sh
    flask run
    ```
    Your application should now be running on `http://127.0.0.1:5000/`.

---

## Usage

Once the application is running:

1.  **Parse a Syllabus:**
    * Navigate to the "Upload Syllabus" or "Import" page.
    * Select a PDF file of a course syllabus (e.g., one from VIT).
    * Click "Upload" and wait for the magic to happen.
    * You will be redirected to your new course page, fully populated.

2.  **Create a Custom Course:**
    * Navigate to the "Create Course" page.
    * Give your course a name (e.g., "Self-Study: Machine Learning").
    * From the course page, add modules and then add topics within each module.

3.  **Track Your Progress:**
    * On your dashboard or course page, find the topic you've finished.
    * Mark its status as "Completed."
    * Watch the progress bar for the module and the overall course update automatically!

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.
