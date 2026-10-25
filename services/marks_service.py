"""
Marks Service Module.
Handles validation, SQL queries, and CRUD operations for the MARKS associative entity.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from database import execute_query, DatabaseIntegrityError, DatabaseError
from services.subject_service import get_subject_by_id


def validate_marks_input(student_id: Any, subject_id: Any, marks_obtained: Any) -> Tuple[bool, str, float]:
    """
    Validate input fields for a marks record.
    Checks:
      1. student_id and subject_id are valid integers.
      2. marks_obtained is numeric and >= 0.
      3. marks_obtained does not exceed the subject's maximum marks.
    Returns (is_valid, error_message, parsed_marks).
    """
    try:
        s_id = int(student_id)
        sub_id = int(subject_id)
    except (ValueError, TypeError):
        return False, "Student and Subject must be selected.", 0.0

    if s_id <= 0 or sub_id <= 0:
        return False, "Please select a valid Student and Subject.", 0.0

    try:
        marks = float(marks_obtained)
    except (ValueError, TypeError):
        return False, "Marks Obtained must be a valid numeric value.", 0.0

    if marks < 0:
        return False, "Marks Obtained cannot be negative (must be >= 0).", 0.0

    # Retrieve subject max marks to validate range in Python
    sub = get_subject_by_id(sub_id)
    if not sub:
        return False, f"Selected Subject ID {sub_id} does not exist in the database.", 0.0

    max_marks = float(sub["max_marks"])
    if marks > max_marks:
        return False, f"Marks Obtained ({marks}) exceeds the maximum marks ({max_marks}) for {sub['subject_name']}.", 0.0

    return True, "", marks


def add_marks(student_id: int, subject_id: int, marks_obtained: Any) -> int:
    """
    Insert a new marks record for a student and subject.
    Enforces that (student_id, subject_id) is unique and marks <= max_marks.
    Returns generated marks_id.
    """
    is_valid, msg, marks = validate_marks_input(student_id, subject_id, marks_obtained)
    if not is_valid:
        raise ValueError(msg)

    # Pre-check for duplicate marks in Python for a clean error message
    dup_sql = "SELECT marks_id FROM marks WHERE student_id = %s AND subject_id = %s;"
    existing = execute_query(dup_sql, (int(student_id), int(subject_id)), fetch="one")
    if existing:
        raise ValueError("A marks record already exists for this Student and Subject. Use Update instead.")

    sql = """
        INSERT INTO marks (student_id, subject_id, marks_obtained)
        VALUES (%s, %s, %s)
        RETURNING marks_id;
    """
    row = execute_query(sql, (int(student_id), int(subject_id), marks), fetch="one")
    return row["marks_id"] if row else 0


def get_all_marks(
    student_id_filter: Optional[int] = None,
    subject_id_filter: Optional[int] = None,
    class_filter: Optional[str] = None,
    division_filter: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve marks records with student and subject details.
    Includes calculated subject percentage.
    Supports filtering by student, subject, class, division, or general search.
    """
    conditions = []
    params: List[Any] = []

    sql = """
        SELECT 
            m.marks_id,
            m.student_id,
            s.name AS student_name,
            s.roll_no,
            s.class_name,
            s.division,
            m.subject_id,
            sub.subject_name,
            sub.max_marks,
            m.marks_obtained,
            ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
        FROM marks m
        INNER JOIN student s ON m.student_id = s.student_id
        INNER JOIN subject sub ON m.subject_id = sub.subject_id
    """

    if student_id_filter and int(student_id_filter) > 0:
        conditions.append("m.student_id = %s")
        params.append(int(student_id_filter))

    if subject_id_filter and int(subject_id_filter) > 0:
        conditions.append("m.subject_id = %s")
        params.append(int(subject_id_filter))

    if class_filter and class_filter.strip() and class_filter.strip().upper() != "ALL":
        conditions.append("s.class_name = %s")
        params.append(class_filter.strip().upper())

    if division_filter and division_filter.strip() and division_filter.strip().upper() != "ALL":
        conditions.append("s.division = %s")
        params.append(division_filter.strip().upper())

    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        conditions.append("(s.name ILIKE %s OR s.roll_no ILIKE %s OR sub.subject_name ILIKE %s)")
        params.extend([q, q, q])

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY s.class_name ASC, s.division ASC, s.roll_no ASC, sub.subject_name ASC;"

    rows = execute_query(sql, tuple(params), fetch="all")
    return rows or []


def get_marks_by_id(marks_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single marks record by primary key."""
    sql = """
        SELECT 
            m.marks_id,
            m.student_id,
            s.name AS student_name,
            s.roll_no,
            s.class_name,
            s.division,
            m.subject_id,
            sub.subject_name,
            sub.max_marks,
            m.marks_obtained
        FROM marks m
        INNER JOIN student s ON m.student_id = s.student_id
        INNER JOIN subject sub ON m.subject_id = sub.subject_id
        WHERE m.marks_id = %s;
    """
    return execute_query(sql, (int(marks_id),), fetch="one")


def update_marks(marks_id: int, marks_obtained: Any) -> bool:
    """
    Update the marks obtained for an existing marks record.
    Pre-validates against the subject's max_marks.
    """
    existing = get_marks_by_id(marks_id)
    if not existing:
        raise ValueError(f"Marks record with ID {marks_id} not found.")

    is_valid, msg, marks = validate_marks_input(existing["student_id"], existing["subject_id"], marks_obtained)
    if not is_valid:
        raise ValueError(msg)

    sql = """
        UPDATE marks
        SET marks_obtained = %s
        WHERE marks_id = %s;
    """
    rowcount = execute_query(sql, (marks, int(marks_id)))
    return rowcount > 0


def delete_marks(marks_id: int) -> bool:
    """Delete a marks record by ID."""
    sql = "DELETE FROM marks WHERE marks_id = %s;"
    rowcount = execute_query(sql, (int(marks_id),))
    return rowcount > 0


def get_student_dropdown_options() -> List[Dict[str, Any]]:
    """
    Retrieve students formatted for GUI comboboxes.
    Returns: list of dicts with student_id, display_label
    """
    sql = """
        SELECT student_id, name, roll_no, class_name, division
        FROM student
        ORDER BY class_name ASC, division ASC, roll_no ASC;
    """
    rows = execute_query(sql, fetch="all") or []
    for r in rows:
        r["display"] = f"[{r['student_id']}] Roll {r['roll_no']}: {r['name']} ({r['class_name']}-{r['division']})"
    return rows


def get_subject_dropdown_options() -> List[Dict[str, Any]]:
    """
    Retrieve subjects formatted for GUI comboboxes.
    Returns: list of dicts with subject_id, subject_name, max_marks, display_label
    """
    sql = """
        SELECT subject_id, subject_name, max_marks
        FROM subject
        ORDER BY subject_name ASC;
    """
    rows = execute_query(sql, fetch="all") or []
    for r in rows:
        r["display"] = f"[{r['subject_id']}] {r['subject_name']} (Max: {r['max_marks']})"
    return rows
