"""
Subject Service Module.
Handles validation, SQL queries, and CRUD operations for the SUBJECT entity.
"""

from typing import List, Dict, Any, Optional, Tuple
from database import execute_query, DatabaseIntegrityError, DatabaseError


def validate_subject_input(subject_name: str, max_marks: Any) -> Tuple[bool, str, int]:
    """
    Validate input fields for a subject record.
    Returns (is_valid, error_message, parsed_max_marks).
    """
    if not subject_name or not subject_name.strip():
        return False, "Subject Name cannot be empty.", 0
    if len(subject_name.strip()) > 100:
        return False, "Subject Name cannot exceed 100 characters.", 0

    try:
        max_m = int(max_marks)
    except (ValueError, TypeError):
        return False, "Maximum Marks must be an integer number.", 0

    if max_m <= 0:
        return False, "Maximum Marks must be strictly greater than 0.", 0

    if max_m > 1000:
        return False, "Maximum Marks cannot exceed 1000.", 0

    return True, "", max_m


def add_subject(subject_name: str, max_marks: Any, subject_id: Optional[int] = None) -> int:
    """
    Insert a new subject into the PostgreSQL database.
    Returns the created subject_id.
    """
    is_valid, msg, max_m = validate_subject_input(subject_name, max_marks)
    if not is_valid:
        raise ValueError(msg)

    name_clean = subject_name.strip()

    if subject_id is not None and int(subject_id) > 0:
        sql = """
            INSERT INTO subject (subject_id, subject_name, max_marks)
            VALUES (%s, %s, %s)
            RETURNING subject_id;
        """
        row = execute_query(sql, (int(subject_id), name_clean, max_m), fetch="one")
    else:
        sql = """
            INSERT INTO subject (subject_name, max_marks)
            VALUES (%s, %s)
            RETURNING subject_id;
        """
        row = execute_query(sql, (name_clean, max_m), fetch="one")

    return row["subject_id"] if row else 0


def get_all_subjects(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all subjects.
    Also aggregates the count of marks records associated with each subject.
    """
    base_sql = """
        SELECT 
            s.subject_id,
            s.subject_name,
            s.max_marks,
            COUNT(m.marks_id) AS marks_count
        FROM subject s
        LEFT JOIN marks m ON s.subject_id = m.subject_id
    """

    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        try:
            num_val = int(search_query.strip())
            sql = base_sql + """
                WHERE s.subject_id = %s OR s.subject_name ILIKE %s
                GROUP BY s.subject_id, s.subject_name, s.max_marks
                ORDER BY s.subject_id ASC;
            """
            return execute_query(sql, (num_val, q), fetch="all")
        except ValueError:
            sql = base_sql + """
                WHERE s.subject_name ILIKE %s
                GROUP BY s.subject_id, s.subject_name, s.max_marks
                ORDER BY s.subject_id ASC;
            """
            return execute_query(sql, (q,), fetch="all")
    else:
        sql = base_sql + """
            GROUP BY s.subject_id, s.subject_name, s.max_marks
            ORDER BY s.subject_id ASC;
        """
        return execute_query(sql, fetch="all")


def get_subject_by_id(subject_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single subject by primary key ID."""
    sql = """
        SELECT subject_id, subject_name, max_marks
        FROM subject
        WHERE subject_id = %s;
    """
    return execute_query(sql, (int(subject_id),), fetch="one")


def update_subject(subject_id: int, subject_name: str, max_marks: Any) -> bool:
    """
    Update subject name and maximum marks.
    Pre-validates that new max_marks is not lower than any existing marks recorded for this subject.
    """
    is_valid, msg, max_m = validate_subject_input(subject_name, max_marks)
    if not is_valid:
        raise ValueError(msg)

    # Pre-check existing marks in Python for clear feedback
    check_sql = "SELECT MAX(marks_obtained) AS highest FROM marks WHERE subject_id = %s;"
    row = execute_query(check_sql, (int(subject_id),), fetch="one")
    if row and row["highest"] is not None:
        highest = float(row["highest"])
        if max_m < highest:
            raise ValueError(
                f"Cannot reduce Maximum Marks to {max_m}. "
                f"Existing marks for this subject reach {highest}. "
                f"Update or remove those student marks records first."
            )

    sql = """
        UPDATE subject
        SET subject_name = %s,
            max_marks = %s
        WHERE subject_id = %s;
    """
    rowcount = execute_query(sql, (subject_name.strip(), max_m, int(subject_id)))
    return rowcount > 0


def delete_subject(subject_id: int) -> bool:
    """
    Delete a subject record.
    If marks records exist for this subject, fk_marks_subject prevents deletion with ON DELETE RESTRICT.
    """
    sql = "DELETE FROM subject WHERE subject_id = %s;"
    rowcount = execute_query(sql, (int(subject_id),))
    return rowcount > 0
