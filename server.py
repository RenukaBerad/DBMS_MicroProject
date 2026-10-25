"""
Internal Marks Management System - Flask Web Backend.
Exposes RESTful APIs and serves the modern Web Dashboard.
Interacts directly with PostgreSQL via services/ and database.py.
"""

import os
import sys
from typing import Any, Dict
from flask import Flask, jsonify, request, render_template, send_from_directory

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import (
    test_connection,
    execute_query,
    DatabaseIntegrityError,
    DatabaseConnectionError,
    DatabaseError
)
import services.student_service as student_service
import services.subject_service as subject_service
import services.marks_service as marks_service
import services.report_service as report_service

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["JSON_SORT_KEYS"] = False


# ==============================================================================
# 1. Page Routes
# ==============================================================================

@app.route("/")
def index():
    """Serve the primary Web Dashboard single-page application."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Verify live PostgreSQL connectivity and return driver details."""
    success, msg = test_connection()
    return jsonify({
        "status": "connected" if success else "disconnected",
        "message": msg,
        "success": success
    }), (200 if success else 503)


# ==============================================================================
# 2. Dashboard KPIs & Overview
# ==============================================================================

@app.route("/api/stats", methods=["GET"])
def get_dashboard_stats():
    """Retrieve all dashboard KPIs and recent records."""
    try:
        stats = report_service.get_dashboard_stats()
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/dropdowns", methods=["GET"])
def get_dropdown_data():
    """Retrieve student, subject, and class dropdown lists for UI forms."""
    try:
        students = marks_service.get_student_dropdown_options()
        subjects = marks_service.get_subject_dropdown_options()
        classes, divisions = student_service.get_distinct_classes_and_divisions()
        return jsonify({
            "success": True,
            "students": students,
            "subjects": subjects,
            "classes": classes,
            "divisions": divisions
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==============================================================================
# 3. Student CRUD APIs
# ==============================================================================

@app.route("/api/students", methods=["GET"])
def list_students():
    """List students with optional search filter."""
    search_q = request.args.get("search", "").strip() or None
    try:
        students = student_service.get_all_students(search_query=search_q)
        return jsonify({"success": True, "data": students, "count": len(students)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/students", methods=["POST"])
def create_student():
    """Add a new student profile."""
    data = request.get_json() or {}
    name = data.get("name", "")
    roll_no = data.get("roll_no", "")
    class_name = data.get("class_name", "")
    division = data.get("division", "")
    student_id = data.get("student_id")

    try:
        cust_id = int(student_id) if student_id and str(student_id).strip() else None
        new_id = student_service.add_student(
            name=name,
            roll_no=roll_no,
            class_name=class_name,
            division=division,
            student_id=cust_id
        )
        return jsonify({
            "success": True,
            "message": f"Student registered successfully with ID: {new_id}",
            "student_id": new_id
        }), 201
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """Update student attributes."""
    data = request.get_json() or {}
    try:
        success = student_service.update_student(
            student_id=student_id,
            name=data.get("name", ""),
            roll_no=data.get("roll_no", ""),
            class_name=data.get("class_name", ""),
            division=data.get("division", "")
        )
        if success:
            return jsonify({"success": True, "message": "Student profile updated successfully."})
        return jsonify({"success": False, "error": "No matching student record found or no changes made."}), 404
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    """Delete a student record with ON DELETE RESTRICT enforcement."""
    try:
        success = student_service.delete_student(student_id)
        if success:
            return jsonify({"success": True, "message": "Student record deleted successfully."})
        return jsonify({"success": False, "error": "Student record not found."}), 404
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==============================================================================
# 4. Subject CRUD APIs
# ==============================================================================

@app.route("/api/subjects", methods=["GET"])
def list_subjects():
    """List subjects with optional search filter."""
    search_q = request.args.get("search", "").strip() or None
    try:
        subjects = subject_service.get_all_subjects(search_query=search_q)
        return jsonify({"success": True, "data": subjects, "count": len(subjects)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/subjects", methods=["POST"])
def create_subject():
    """Add a new subject."""
    data = request.get_json() or {}
    name = data.get("subject_name", "")
    max_marks = data.get("max_marks", 100)
    subject_id = data.get("subject_id")

    try:
        cust_id = int(subject_id) if subject_id and str(subject_id).strip() else None
        new_id = subject_service.add_subject(
            subject_name=name,
            max_marks=max_marks,
            subject_id=cust_id
        )
        return jsonify({
            "success": True,
            "message": f"Subject created successfully with ID: {new_id}",
            "subject_id": new_id
        }), 201
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/subjects/<int:subject_id>", methods=["PUT"])
def update_subject(subject_id):
    """Update subject title and max_marks."""
    data = request.get_json() or {}
    try:
        success = subject_service.update_subject(
            subject_id=subject_id,
            subject_name=data.get("subject_name", ""),
            max_marks=data.get("max_marks", 100)
        )
        if success:
            return jsonify({"success": True, "message": "Subject updated successfully."})
        return jsonify({"success": False, "error": "Subject not found or no changes made."}), 404
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
def delete_subject(subject_id):
    """Delete a subject record with ON DELETE RESTRICT enforcement."""
    try:
        success = subject_service.delete_subject(subject_id)
        if success:
            return jsonify({"success": True, "message": "Subject deleted successfully."})
        return jsonify({"success": False, "error": "Subject not found."}), 404
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==============================================================================
# 5. Marks CRUD APIs
# ==============================================================================

@app.route("/api/marks", methods=["GET"])
def list_marks():
    """List marks with extensive filter support."""
    student_id = request.args.get("student_id", type=int)
    subject_id = request.args.get("subject_id", type=int)
    class_filter = request.args.get("class", "").strip() or None
    division_filter = request.args.get("division", "").strip() or None
    search_q = request.args.get("search", "").strip() or None

    try:
        marks = marks_service.get_all_marks(
            student_id_filter=student_id,
            subject_id_filter=subject_id,
            class_filter=class_filter,
            division_filter=division_filter,
            search_query=search_q
        )
        return jsonify({"success": True, "data": marks, "count": len(marks)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/marks", methods=["POST"])
def create_marks():
    """Assign marks to a student for a subject."""
    data = request.get_json() or {}
    try:
        student_id = int(data.get("student_id"))
        subject_id = int(data.get("subject_id"))
        marks_obtained = data.get("marks_obtained")

        marks_id = marks_service.add_marks(
            student_id=student_id,
            subject_id=subject_id,
            marks_obtained=marks_obtained
        )
        return jsonify({
            "success": True,
            "message": f"Marks recorded successfully with ID: {marks_id}",
            "marks_id": marks_id
        }), 201
    except (ValueError, TypeError) as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/marks/<int:marks_id>", methods=["PUT"])
def update_marks(marks_id):
    """Update marks obtained score."""
    data = request.get_json() or {}
    try:
        marks_obtained = data.get("marks_obtained")
        success = marks_service.update_marks(
            marks_id=marks_id,
            marks_obtained=marks_obtained
        )
        if success:
            return jsonify({"success": True, "message": "Marks score updated successfully."})
        return jsonify({"success": False, "error": "Marks record not found or no changes made."}), 404
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except DatabaseIntegrityError as die:
        return jsonify({"success": False, "error": str(die)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/marks/<int:marks_id>", methods=["DELETE"])
def delete_marks(marks_id):
    """Delete a marks record."""
    try:
        success = marks_service.delete_marks(marks_id)
        if success:
            return jsonify({"success": True, "message": "Marks record deleted successfully."})
        return jsonify({"success": False, "error": "Marks record not found."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==============================================================================
# 6. Results & Analytical Reports APIs
# ==============================================================================

@app.route("/api/results/student/<int:student_id>", methods=["GET"])
def get_student_marksheet(student_id):
    """Generate comprehensive marksheet for a student."""
    try:
        result = report_service.get_student_result(student_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/results/subject/<int:subject_id>", methods=["GET"])
def get_subject_performance(subject_id):
    """Retrieve detailed subject-level score distribution and metrics."""
    try:
        result = report_service.get_subject_performance(subject_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/student-wise", methods=["GET"])
def report_student_wise():
    """Report 1: Student-wise marks list with filters."""
    class_filter = request.args.get("class", "").strip() or None
    div_filter = request.args.get("division", "").strip() or None
    sub_id = request.args.get("subject_id", type=int)

    try:
        data = report_service.get_report_student_wise_marks(
            class_filter=class_filter,
            division_filter=div_filter,
            subject_id_filter=sub_id
        )
        return jsonify({"success": True, "data": data, "count": len(data)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/subject-performance", methods=["GET"])
def report_subject_performance():
    """Report 2: Subject-wise aggregated analytics."""
    try:
        data = report_service.get_report_subject_performance()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/class-summary", methods=["GET"])
def report_class_summary():
    """Report 3: Class and division summary."""
    try:
        data = report_service.get_report_class_division_summary()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/without-marks", methods=["GET"])
def report_without_marks():
    """Report 4: Students without any marks records."""
    try:
        data = report_service.get_report_students_without_marks()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==============================================================================
# 7. Interactive SQL Console & Demo Queries
# ==============================================================================

PRESET_QUERIES = [
    {
        "id": "q1",
        "title": "1. Student Full Marksheet (INNER JOIN)",
        "sql": """SELECT s.student_id, s.name, s.roll_no, s.class_name, s.division,
       sub.subject_name, m.marks_obtained, sub.max_marks,
       ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
FROM marks m
JOIN student s ON m.student_id = s.student_id
JOIN subject sub ON m.subject_id = sub.subject_id
ORDER BY s.roll_no, sub.subject_id;"""
    },
    {
        "id": "q2",
        "title": "2. Subject Performance & Aggregates (COUNT, AVG, MIN, MAX)",
        "sql": """SELECT sub.subject_id, sub.subject_name, sub.max_marks,
       COUNT(m.marks_id) AS evaluated_students,
       ROUND(AVG(m.marks_obtained), 2) AS average_score,
       MAX(m.marks_obtained) AS highest_score,
       MIN(m.marks_obtained) AS lowest_score,
       ROUND((AVG(m.marks_obtained) / sub.max_marks) * 100.0, 2) AS average_percentage
FROM subject sub
LEFT JOIN marks m ON sub.subject_id = m.subject_id
GROUP BY sub.subject_id, sub.subject_name, sub.max_marks
ORDER BY sub.subject_id;"""
    },
    {
        "id": "q3",
        "title": "3. Class & Division Performance Comparison",
        "sql": """SELECT s.class_name, s.division,
       COUNT(DISTINCT s.student_id) AS total_students,
       COUNT(m.marks_id) AS total_evaluations,
       ROUND(AVG((m.marks_obtained / sub.max_marks) * 100.0), 2) AS class_average_percentage
FROM student s
LEFT JOIN marks m ON s.student_id = m.student_id
LEFT JOIN subject sub ON m.subject_id = sub.subject_id
GROUP BY s.class_name, s.division
ORDER BY s.class_name, s.division;"""
    },
    {
        "id": "q4",
        "title": "4. Students with No Marks Recorded (LEFT JOIN with IS NULL)",
        "sql": """SELECT s.student_id, s.name, s.roll_no, s.class_name, s.division
FROM student s
LEFT JOIN marks m ON s.student_id = m.student_id
WHERE m.marks_id IS NULL
ORDER BY s.class_name, s.division, s.roll_no;"""
    },
    {
        "id": "q5",
        "title": "5. Top Scorers per Subject (> 85% Distinction)",
        "sql": """SELECT s.name, s.roll_no, s.class_name, sub.subject_name,
       m.marks_obtained, sub.max_marks,
       ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS pct
FROM marks m
JOIN student s ON m.student_id = s.student_id
JOIN subject sub ON m.subject_id = sub.subject_id
WHERE (m.marks_obtained / sub.max_marks) >= 0.85
ORDER BY pct DESC;"""
    }
]


@app.route("/api/sql/presets", methods=["GET"])
def get_preset_queries():
    """Retrieve pre-built viva demonstration queries."""
    return jsonify({"success": True, "presets": PRESET_QUERIES})


@app.route("/api/sql/execute", methods=["POST"])
def execute_custom_sql():
    """
    Execute read-only SQL queries safely for faculty viva demonstration.
    Rejects DROP, TRUNCATE, DELETE, UPDATE, ALTER statements to protect database integrity.
    """
    data = request.get_json() or {}
    raw_query = data.get("query", "").strip()

    if not raw_query:
        return jsonify({"success": False, "error": "Query cannot be empty."}), 400

    # Safety guard: only allow SELECT or EXPLAIN statements
    cleaned = raw_query.upper().strip()
    if not (cleaned.startswith("SELECT") or cleaned.startswith("EXPLAIN") or cleaned.startswith("WITH")):
        return jsonify({
            "success": False,
            "error": "Security Guard: The interactive console only permits read-only analytical queries (SELECT, WITH, EXPLAIN). DDL/DML mutations must be executed through the entity management forms."
        }), 403

    try:
        rows = execute_query(raw_query, fetch="all")
        columns = list(rows[0].keys()) if rows else []
        return jsonify({
            "success": True,
            "columns": columns,
            "rows": rows,
            "count": len(rows)
        })
    except DatabaseError as de:
        return jsonify({"success": False, "error": str(de)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==============================================================================
# Main Runner
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    is_debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"\n========================================================")
    print(f"  INTERNAL MARKS MANAGEMENT SYSTEM - WEB DASHBOARD")
    print(f"  Live at: http://{host}:{port}")
    print(f"========================================================\n")
    app.run(host=host, port=port, debug=is_debug)
