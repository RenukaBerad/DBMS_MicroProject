"""
Report Service Module.
Executes live SQL queries for dashboard statistics, student results,
subject performance, and multi-table analytical reports.
"""

from typing import List, Dict, Any, Optional
from database import execute_query


def get_dashboard_stats() -> Dict[str, Any]:
    """
    Retrieve live dashboard KPI counts and summary metrics using SQL.
    Returns:
      total_students, total_subjects, total_marks_records,
      students_with_marks, students_without_marks, overall_average_percentage,
      recent_marks
    """
    # Main aggregated metrics in a single efficient query
    stats_sql = """
        SELECT 
            (SELECT COUNT(*) FROM student) AS total_students,
            (SELECT COUNT(*) FROM subject) AS total_subjects,
            (SELECT COUNT(*) FROM marks) AS total_marks_records,
            (SELECT COUNT(DISTINCT student_id) FROM marks) AS students_with_marks,
            (SELECT COUNT(*) FROM student s WHERE NOT EXISTS (
                SELECT 1 FROM marks m WHERE m.student_id = s.student_id
            )) AS students_without_marks,
            (SELECT COALESCE(ROUND(AVG((m.marks_obtained / sub.max_marks) * 100.0), 2), 0.00) 
             FROM marks m 
             JOIN subject sub ON m.subject_id = sub.subject_id) AS overall_average_percentage;
    """
    stats = execute_query(stats_sql, fetch="one") or {}

    # Recent marks entries (last 6 records)
    recent_sql = """
        SELECT 
            m.marks_id,
            s.name AS student_name,
            s.roll_no,
            s.class_name,
            s.division,
            sub.subject_name,
            m.marks_obtained,
            sub.max_marks,
            ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
        FROM marks m
        INNER JOIN student s ON m.student_id = s.student_id
        INNER JOIN subject sub ON m.subject_id = sub.subject_id
        ORDER BY m.marks_id DESC
        LIMIT 6;
    """
    recent_marks = execute_query(recent_sql, fetch="all") or []

    # Recent student entries (last 6 students registered)
    recent_students_sql = """
        SELECT 
            s.student_id,
            s.name,
            s.roll_no,
            s.class_name,
            s.division,
            (SELECT COUNT(*) FROM marks m WHERE m.student_id = s.student_id) AS marks_count
        FROM student s
        ORDER BY s.student_id DESC
        LIMIT 6;
    """
    recent_students = execute_query(recent_students_sql, fetch="all") or []

    return {
        "total_students": stats.get("total_students", 0),
        "total_subjects": stats.get("total_subjects", 0),
        "total_marks_records": stats.get("total_marks_records", 0),
        "students_with_marks": stats.get("students_with_marks", 0),
        "students_without_marks": stats.get("students_without_marks", 0),
        "overall_average_percentage": float(stats.get("overall_average_percentage", 0.0) or 0.0),
        "recent_marks": recent_marks,
        "recent_students": recent_students
    }


def get_student_result(student_id: int) -> Dict[str, Any]:
    """
    Generate student marksheet and summary result from live PostgreSQL queries.
    Returns:
      student: student metadata dict
      subject_marks: list of subject-wise marks and percentages
      summary: total_obtained, total_max, overall_percentage, subjects_count
    """
    student_sql = """
        SELECT student_id, name, roll_no, class_name, division
        FROM student
        WHERE student_id = %s;
    """
    student = execute_query(student_sql, (int(student_id),), fetch="one")
    if not student:
        return {"student": None, "subject_marks": [], "summary": {}}

    marks_sql = """
        SELECT 
            sub.subject_id,
            sub.subject_name,
            sub.max_marks,
            m.marks_obtained,
            ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
        FROM marks m
        INNER JOIN subject sub ON m.subject_id = sub.subject_id
        WHERE m.student_id = %s
        ORDER BY sub.subject_id ASC;
    """
    subject_marks = execute_query(marks_sql, (int(student_id),), fetch="all") or []

    # Calculate overall summary
    total_obtained = sum(float(r["marks_obtained"]) for r in subject_marks)
    total_max = sum(int(r["max_marks"]) for r in subject_marks)
    overall_pct = round((total_obtained / total_max) * 100.0, 2) if total_max > 0 else 0.0

    summary = {
        "subjects_count": len(subject_marks),
        "total_obtained": round(total_obtained, 2),
        "total_max": total_max,
        "overall_percentage": overall_pct
    }

    return {
        "student": student,
        "subject_marks": subject_marks,
        "summary": summary
    }


def get_subject_performance(subject_id: int) -> Dict[str, Any]:
    """
    Retrieve subject analytics, scores, and distribution from live PostgreSQL queries.
    Returns:
      subject: subject metadata dict
      student_scores: list of student marks in this subject
      metrics: student_count, avg_marks, max_marks_obtained, min_marks_obtained, avg_percentage
    """
    sub_sql = "SELECT subject_id, subject_name, max_marks FROM subject WHERE subject_id = %s;"
    subject = execute_query(sub_sql, (int(subject_id),), fetch="one")
    if not subject:
        return {"subject": None, "student_scores": [], "metrics": {}}

    scores_sql = """
        SELECT 
            s.student_id,
            s.name AS student_name,
            s.roll_no,
            s.class_name,
            s.division,
            m.marks_obtained,
            ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
        FROM marks m
        INNER JOIN student s ON m.student_id = s.student_id
        INNER JOIN subject sub ON m.subject_id = sub.subject_id
        WHERE m.subject_id = %s
        ORDER BY m.marks_obtained DESC;
    """
    student_scores = execute_query(scores_sql, (int(subject_id),), fetch="all") or []

    if student_scores:
        scores = [float(r["marks_obtained"]) for r in student_scores]
        max_possible = float(subject["max_marks"])
        avg_score = round(sum(scores) / len(scores), 2)
        metrics = {
            "student_count": len(scores),
            "average_marks": avg_score,
            "highest_marks": max(scores),
            "lowest_marks": min(scores),
            "average_percentage": round((avg_score / max_possible) * 100.0, 2) if max_possible > 0 else 0.0
        }
    else:
        metrics = {
            "student_count": 0,
            "average_marks": 0.0,
            "highest_marks": 0.0,
            "lowest_marks": 0.0,
            "average_percentage": 0.0
        }

    return {
        "subject": subject,
        "student_scores": student_scores,
        "metrics": metrics
    }


def get_report_student_wise_marks(
    class_filter: Optional[str] = None,
    division_filter: Optional[str] = None,
    subject_id_filter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Report 1: Student-wise Marks Report.
    Demonstrates: SELECT, JOIN, WHERE, ORDER BY, calculated columns.
    """
    conditions = []
    params: List[Any] = []

    sql = """
        SELECT 
            s.student_id,
            s.name AS student_name,
            s.roll_no,
            s.class_name,
            s.division,
            sub.subject_name,
            sub.max_marks,
            m.marks_obtained,
            ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
        FROM marks m
        INNER JOIN student s ON m.student_id = s.student_id
        INNER JOIN subject sub ON m.subject_id = sub.subject_id
    """

    if class_filter and class_filter.strip().upper() != "ALL":
        conditions.append("s.class_name = %s")
        params.append(class_filter.strip().upper())

    if division_filter and division_filter.strip().upper() != "ALL":
        conditions.append("s.division = %s")
        params.append(division_filter.strip().upper())

    if subject_id_filter and int(subject_id_filter) > 0:
        conditions.append("m.subject_id = %s")
        params.append(int(subject_id_filter))

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY s.class_name ASC, s.division ASC, s.roll_no ASC, sub.subject_name ASC;"

    return execute_query(sql, tuple(params), fetch="all") or []


def get_report_subject_performance() -> List[Dict[str, Any]]:
    """
    Report 2: Subject-wise Performance Report.
    Demonstrates: JOIN, COUNT, AVG, MAX, MIN, GROUP BY.
    """
    sql = """
        SELECT 
            sub.subject_id,
            sub.subject_name,
            sub.max_marks,
            COUNT(m.marks_id) AS total_records,
            COALESCE(ROUND(AVG(m.marks_obtained), 2), 0.00) AS average_marks,
            COALESCE(MAX(m.marks_obtained), 0.00) AS highest_marks,
            COALESCE(MIN(m.marks_obtained), 0.00) AS lowest_marks,
            COALESCE(ROUND((AVG(m.marks_obtained) / NULLIF(sub.max_marks, 0)) * 100.0, 2), 0.00) AS average_percentage
        FROM subject sub
        LEFT JOIN marks m ON sub.subject_id = m.subject_id
        GROUP BY sub.subject_id, sub.subject_name, sub.max_marks
        ORDER BY sub.subject_id ASC;
    """
    return execute_query(sql, fetch="all") or []


def get_report_class_division_summary() -> List[Dict[str, Any]]:
    """
    Report 3: Class and Division Summary.
    Avoids duplicate-count errors by using COUNT(DISTINCT s.student_id).
    Demonstrates: JOIN, GROUP BY, COUNT, AVG, and sorting.
    """
    sql = """
        SELECT 
            s.class_name,
            s.division,
            COUNT(DISTINCT s.student_id) AS total_students,
            COUNT(m.marks_id) AS total_marks_records,
            COALESCE(ROUND(AVG((m.marks_obtained / sub.max_marks) * 100.0), 2), 0.00) AS average_percentage
        FROM student s
        LEFT JOIN marks m ON s.student_id = m.student_id
        LEFT JOIN subject sub ON m.subject_id = sub.subject_id
        GROUP BY s.class_name, s.division
        ORDER BY s.class_name ASC, s.division ASC;
    """
    return execute_query(sql, fetch="all") or []


def get_report_students_without_marks() -> List[Dict[str, Any]]:
    """
    Supplementary Report: Students with no marks recorded.
    Demonstrates: LEFT JOIN and WHERE m.marks_id IS NULL.
    """
    sql = """
        SELECT 
            s.student_id,
            s.name AS student_name,
            s.roll_no,
            s.class_name,
            s.division
        FROM student s
        LEFT JOIN marks m ON s.student_id = m.student_id
        WHERE m.marks_id IS NULL
        ORDER BY s.class_name ASC, s.division ASC, s.roll_no ASC;
    """
    return execute_query(sql, fetch="all") or []
