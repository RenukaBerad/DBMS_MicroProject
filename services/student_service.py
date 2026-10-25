"""
Student Service Module.
Handles validation, SQL queries, and CRUD operations for the STUDENT entity.
"""

from typing import List, Dict, Any, Optional, Tuple
from database import execute_query, DatabaseIntegrityError, DatabaseError


def validate_student_input(name: str, roll_no: str, class_name: str, division: str) -> Tuple[bool, str]:
    """
    Validate input fields for a student record.
    Returns (True, "") or (False, error_message).
    """
    if not name or not name.strip():
        return False, "Student Name cannot be empty."
    if len(name.strip()) > 100:
        return False, "Student Name cannot exceed 100 characters."

    if not roll_no or not roll_no.strip():
        return False, "Roll Number cannot be empty."
    if len(roll_no.strip()) > 20:
        return False, "Roll Number cannot exceed 20 characters."

    if not class_name or not class_name.strip():
        return False, "Class cannot be empty."
    if len(class_name.strip()) > 50:
        return False, "Class cannot exceed 50 characters."

    if not division or not division.strip():
        return False, "Division cannot be empty."
    if len(division.strip()) > 10:
        return False, "Division cannot exceed 10 characters."

    return True, ""


def add_student(name: str, roll_no: str, class_name: str, division: str, student_id: Optional[int] = None) -> int:
    """
    Insert a new student record into the PostgreSQL database.
    Returns the generated or assigned student_id.
    """
    is_valid, msg = validate_student_input(name, roll_no, class_name, division)
    if not is_valid:
        raise ValueError(msg)

    name_clean = name.strip()
    roll_clean = roll_no.strip()
    class_clean = class_name.strip().upper()
    div_clean = division.strip().upper()

    if student_id is not None and int(student_id) > 0:
        sql = """
            INSERT INTO student (student_id, name, roll_no, class_name, division)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING student_id;
        """
        row = execute_query(sql, (int(student_id), name_clean, roll_clean, class_clean, div_clean), fetch="one")
    else:
        sql = """
            INSERT INTO student (name, roll_no, class_name, division)
            VALUES (%s, %s, %s, %s)
            RETURNING student_id;
        """
        row = execute_query(sql, (name_clean, roll_clean, class_clean, div_clean), fetch="one")

    return row["student_id"] if row else 0


def get_all_students(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve students sorted by class, division, and roll number.
    Optionally filters by ID, name, roll number, class, or division.
    """
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        # Check if search term is numeric for direct ID check
        try:
            num_val = int(search_query.strip())
            sql = """
                SELECT student_id, name, roll_no, class_name, division
                FROM student
                WHERE student_id = %s
                   OR name ILIKE %s
                   OR roll_no ILIKE %s
                   OR class_name ILIKE %s
                   OR division ILIKE %s
                ORDER BY class_name ASC, division ASC, roll_no ASC;
            """
            return execute_query(sql, (num_val, q, q, q, q), fetch="all")
        except ValueError:
            sql = """
                SELECT student_id, name, roll_no, class_name, division
                FROM student
                WHERE name ILIKE %s
                   OR roll_no ILIKE %s
                   OR class_name ILIKE %s
                   OR division ILIKE %s
                ORDER BY class_name ASC, division ASC, roll_no ASC;
            """
            return execute_query(sql, (q, q, q, q), fetch="all")
    else:
        sql = """
            SELECT student_id, name, roll_no, class_name, division
            FROM student
            ORDER BY class_name ASC, division ASC, roll_no ASC;
        """
        return execute_query(sql, fetch="all")


def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single student by primary key ID."""
    sql = """
        SELECT student_id, name, roll_no, class_name, division
        FROM student
        WHERE student_id = %s;
    """
    return execute_query(sql, (int(student_id),), fetch="one")


def update_student(student_id: int, name: str, roll_no: str, class_name: str, division: str) -> bool:
    """
    Update an existing student's attributes in PostgreSQL.
    """
    is_valid, msg = validate_student_input(name, roll_no, class_name, division)
    if not is_valid:
        raise ValueError(msg)

    sql = """
        UPDATE student
        SET name = %s,
            roll_no = %s,
            class_name = %s,
            division = %s
        WHERE student_id = %s;
    """
    rowcount = execute_query(
        sql,
        (name.strip(), roll_no.strip(), class_name.strip().upper(), division.strip().upper(), int(student_id))
    )
    return rowcount > 0


def delete_student(student_id: int) -> bool:
    """
    Delete a student record.
    If marks records exist for this student, the foreign key constraint
    fk_marks_student with ON DELETE RESTRICT prevents deletion, raising DatabaseIntegrityError.
    """
    sql = "DELETE FROM student WHERE student_id = %s;"
    rowcount = execute_query(sql, (int(student_id),))
    return rowcount > 0


def get_distinct_classes_and_divisions() -> Tuple[List[str], List[str]]:
    """Return lists of distinct classes and divisions present in the database."""
    classes = execute_query("SELECT DISTINCT class_name FROM student ORDER BY class_name ASC;", fetch="all")
    divisions = execute_query("SELECT DISTINCT division FROM student ORDER BY division ASC;", fetch="all")
    c_list = [c["class_name"] for c in classes] if classes else []
    d_list = [d["division"] for d in divisions] if divisions else []
    return c_list, d_list
