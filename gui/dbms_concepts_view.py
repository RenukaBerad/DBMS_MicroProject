"""
DBMS Concepts & Viva Guide View Module.
Provides interactive visual explanations of:
  1. ER Model & Entity Relationships (Strong vs Associative)
  2. Relational Schema & Constraints (PK, FK, UNIQUE, CHECK, Triggers)
  3. Database Normalization (1NF -> 2NF -> 3NF Progression)
  4. SQL DDL, DML & Demonstration Queries Reference
"""

import tkinter as tk
from tkinter import ttk


class DBMSConceptsView(ttk.Frame):
    """
    In-app viva preparation and DBMS concepts explorer.
    """

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, style="Content.TFrame")
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self, style="Content.TFrame")
        header.pack(fill=tk.X, padx=25, pady=(20, 10))

        title_lbl = ttk.Label(
            header,
            text="DBMS Concepts, Schema & Normalization",
            font=("Segoe UI", 18, "bold"),
            foreground="#0F172A",
            background="#F8FAFC"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            header,
            text="Theoretical foundations, relational mapping, and viva explanations for faculty evaluation",
            font=("Segoe UI", 10),
            foreground="#64748B",
            background="#F8FAFC"
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Notebook tabs
        notebook_frame = ttk.Frame(self, style="Content.TFrame")
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: ER & Relational Model
        tab_er = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(tab_er, text="  📐 ER Model & Relationships  ")
        self._build_er_tab(tab_er)

        # Tab 2: Normalization (1NF to 3NF)
        tab_norm = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(tab_norm, text="  🔄 Normalization (1NF → 3NF)  ")
        self._build_normalization_tab(tab_norm)

        # Tab 3: Keys, Constraints & Triggers
        tab_keys = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(tab_keys, text="  🛡️ Integrity Constraints & Triggers  ")
        self._build_constraints_tab(tab_keys)

        # Tab 4: SQL Query Reference
        tab_sql = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(tab_sql, text="  💻 SQL Queries Reference  ")
        self._build_sql_tab(tab_sql)

    def _create_scrollable_text(self, parent: ttk.Frame, content: str):
        """Create a clean, read-only text container with scrollbar."""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        txt = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#1E293B",
            padx=16,
            pady=16,
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=scrollbar.set)

        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        txt.insert(tk.END, content)
        txt.config(state="disabled")

    def _build_er_tab(self, parent: ttk.Frame):
        er_content = """
========================================================================================
1. ENTITY-RELATIONSHIP (ER) MODEL & ARCHITECTURE
========================================================================================

A. STRONG ENTITIES:
   1. STUDENT
      - Independent entity representing enrolled students.
      - Key Attribute: student_id (Primary Key)
      - Descriptive Attributes: name, roll_no, class (mapped to class_name), division.
      - Uniqueness: UNIQUE(class_name, division, roll_no)

   2. SUBJECT
      - Independent entity representing academic curriculum subjects.
      - Key Attribute: subject_id (Primary Key)
      - Descriptive Attributes: subject_name, max_marks.
      - Domain Constraint: CHECK (max_marks > 0)

B. ASSOCIATIVE ENTITY (RESOLVING MANY-TO-MANY RELATIONSHIP):
   3. MARKS
      - Conceptually, a Student studies multiple Subjects, and a Subject is taken by
        multiple Students (M:N Relationship).
      - In relational databases, a direct Many-to-Many relationship cannot be represented
        efficiently without introducing data redundancy or repeating groups.
      - The associative entity MARKS resolves this M:N relationship into two clean
        1:N relationships:
           • STUDENT (1) ────< (N) MARKS
           • SUBJECT (1) ────< (N) MARKS
      - Key Attribute: marks_id (Primary Key)
      - Foreign Keys:
           • student_id references student(student_id)
           • subject_id references subject(subject_id)
      - Descriptive Attribute: marks_obtained
      - Candidate Key / Uniqueness: UNIQUE(student_id, subject_id) ensures each student
        has at most one recorded marks entry per subject.

========================================================================================
2. ER-TO-RELATIONAL MAPPING PROCEDURE
========================================================================================
Step 1: Map Regular Strong Entities:
   - STUDENT -> Table `student` (student_id PK, name, roll_no, class_name, division)
   - SUBJECT -> Table `subject` (subject_id PK, subject_name, max_marks)

Step 2: Map Binary M:N Relationship with Attributes:
   - Create Table `marks` (marks_id PK, student_id FK, subject_id FK, marks_obtained)
   - Include Foreign Keys referencing parent primary keys with ON DELETE RESTRICT
   - Add UNIQUE(student_id, subject_id) to model functional dependency.
"""
        self._create_scrollable_text(parent, er_content)

    def _build_normalization_tab(self, parent: ttk.Frame):
        norm_content = """
========================================================================================
DATABASE NORMALIZATION (1NF → 2NF → 3NF PROGRESSION)
========================================================================================

The database design strictly follows relational normalization theory to eliminate
insertion, update, and deletion anomalies.

----------------------------------------------------------------------------------------
0. UNNORMALIZED FORM (UNF) - TYPICAL FLAT SPREADSHEET
----------------------------------------------------------------------------------------
Initial unnormalized structure:
STUDENT_MARKS_SHEET (
    roll_no, name, class, division,
    { subject_name, max_marks, marks_obtained }  <-- Repeating group of subjects
)
• Anomalies:
  - Repeating groups of subjects.
  - Non-atomic multi-valued cells.

----------------------------------------------------------------------------------------
1. FIRST NORMAL FORM (1NF) - ATOMICITY & NO REPEATING GROUPS
----------------------------------------------------------------------------------------
Rule: Each attribute must contain only atomic (indivisible) values, and each record
      must have a distinct primary key.

Flattened 1NF Table:
ENROLLMENT_1NF (
    roll_no, class, division, name, subject_name, max_marks, marks_obtained
)
Composite Primary Key: (roll_no, class, division, subject_name)

• Anomalies remaining in 1NF:
  - Redundancy: Student 'name' is repeated for every subject taken.
  - Redundancy: Subject 'max_marks' is repeated for every student taking that subject.
  - Partial Functional Dependencies exist!

----------------------------------------------------------------------------------------
2. SECOND NORMAL FORM (2NF) - REMOVAL OF PARTIAL DEPENDENCIES
----------------------------------------------------------------------------------------
Rule: Must be in 1NF, AND every non-prime attribute must be fully functionally dependent
      on the entire primary key (no partial dependencies on a subset of composite key).

Functional Dependencies in 1NF:
  1. (roll_no, class, division) -> name               [Partial Dependency!]
  2. subject_name -> max_marks                        [Partial Dependency!]
  3. (roll_no, class, division, subject_name) -> marks_obtained [Full Dependency]

Decomposition into 2NF:
  • STUDENT (student_id PK, name, roll_no, class_name, division)
  • SUBJECT (subject_id PK, subject_name, max_marks)
  • MARKS (marks_id PK, student_id FK, subject_id FK, marks_obtained)

----------------------------------------------------------------------------------------
3. THIRD NORMAL FORM (3NF) - REMOVAL OF TRANSITIVE DEPENDENCIES
----------------------------------------------------------------------------------------
Rule: Must be in 2NF, AND no non-prime attribute should be transitively dependent on
      the primary key (for X -> A, either X is a superkey or A is a prime attribute).

Analysis of 2NF Tables:
  • In STUDENT: student_id -> {roll_no, class_name, division, name}
    There are no transitive dependencies among non-prime attributes.
  • In SUBJECT: subject_id -> {subject_name, max_marks}
    No transitive dependencies exist.
  • In MARKS: marks_id -> {student_id, subject_id, marks_obtained}
    No transitive dependencies exist.

Conclusion:
The final 3-table schema [student, subject, marks] is in 3NF (and BCNF),
guaranteeing minimal redundancy, zero insertion/update/deletion anomalies,
and maximum data integrity!
"""
        self._create_scrollable_text(parent, norm_content)

    def _build_constraints_tab(self, parent: ttk.Frame):
        keys_content = """
========================================================================================
DATABASE INTEGRITY CONSTRAINTS & BUSINESS RULES
========================================================================================

1. PRIMARY KEY CONSTRAINTS:
   - student.student_id : SERIAL PRIMARY KEY (Unique, NOT NULL, surrogate key)
   - subject.subject_id : SERIAL PRIMARY KEY (Unique, NOT NULL, surrogate key)
   - marks.marks_id     : SERIAL PRIMARY KEY (Unique, NOT NULL, transaction ID)

2. FOREIGN KEY CONSTRAINTS & DELETION POLICIES:
   - fk_marks_student: marks(student_id) REFERENCES student(student_id)
     ON DELETE RESTRICT ON UPDATE CASCADE
   - fk_marks_subject: marks(subject_id) REFERENCES subject(subject_id)
     ON DELETE RESTRICT ON UPDATE CASCADE
   • Purpose of ON DELETE RESTRICT:
     Prevents accidental deletion of a student or subject if marks records exist.
     Ensures historical assessment data cannot be orphaned.

3. UNIQUE CONSTRAINTS:
   - uq_student_roll on student(class_name, division, roll_no):
     Ensures that no two students have the same roll number in the same division.
   - uq_student_subject on marks(student_id, subject_id):
     Ensures that each student receives only one marks record per subject.
   - subject_name UNIQUE:
     Prevents creating duplicate subject names in curriculum.

4. CHECK CONSTRAINTS:
   - subject.max_marks: CHECK (max_marks > 0)
   - marks.marks_obtained: CHECK (marks_obtained >= 0)

5. POSTGRESQL CROSS-TABLE TRIGGERS (DATABASE-LEVEL INTEGRITY):
   - Trigger: trg_check_marks_before_insert_or_update
     Function: check_marks_within_max()
     Why needed: Standard SQL column CHECK constraints cannot compare values against
     another table. This PL/pgSQL trigger verifies in PostgreSQL that:
     NEW.marks_obtained <= subject.max_marks
     before committing an INSERT or UPDATE on the marks table!

   - Trigger: trg_check_subject_max_marks
     Function: check_subject_max_marks_update()
     Why needed: Prevents an administrator from reducing a subject's max_marks
     if any existing marks in the database already exceed the proposed lower maximum.
"""
        self._create_scrollable_text(parent, keys_content)

    def _build_sql_tab(self, parent: ttk.Frame):
        sql_content = """
========================================================================================
SQL DEMONSTRATION & CORE OPERATIONS (RUNNABLE AGAINST SCHEMA)
========================================================================================

1. THREE-TABLE INNER JOIN (Student Marks Ledger):
----------------------------------------------------------------------------------------
SELECT 
    s.student_id, s.name, s.roll_no, s.class_name, s.division,
    sub.subject_name, sub.max_marks, m.marks_obtained,
    ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
FROM marks m
INNER JOIN student s ON m.student_id = s.student_id
INNER JOIN subject sub ON m.subject_id = sub.subject_id
ORDER BY s.class_name, s.division, s.roll_no;

2. AGGREGATES & GROUP BY (Subject-wise Performance):
----------------------------------------------------------------------------------------
SELECT 
    sub.subject_name,
    COUNT(m.marks_id) AS total_students,
    ROUND(AVG(m.marks_obtained), 2) AS avg_marks,
    MAX(m.marks_obtained) AS highest_marks,
    MIN(m.marks_obtained) AS lowest_marks,
    ROUND((AVG(m.marks_obtained) / sub.max_marks) * 100.0, 2) AS avg_pct
FROM subject sub
LEFT JOIN marks m ON sub.subject_id = m.subject_id
GROUP BY sub.subject_id, sub.subject_name, sub.max_marks;

3. LEFT OUTER JOIN (Detecting Students With No Marks):
----------------------------------------------------------------------------------------
SELECT s.student_id, s.name, s.roll_no, s.class_name, s.division
FROM student s
LEFT JOIN marks m ON s.student_id = m.student_id
WHERE m.marks_id IS NULL;

4. STUDENT RESULT & OVERALL PERCENTAGE:
----------------------------------------------------------------------------------------
SELECT 
    s.name,
    COUNT(m.marks_id) AS evaluated_subjects,
    SUM(m.marks_obtained) AS total_marks_obtained,
    SUM(sub.max_marks) AS total_max_marks,
    ROUND((SUM(m.marks_obtained) / SUM(sub.max_marks)) * 100.0, 2) AS overall_percentage
FROM student s
JOIN marks m ON s.student_id = m.student_id
JOIN subject sub ON m.subject_id = sub.subject_id
WHERE s.student_id = 1
GROUP BY s.student_id, s.name;
"""
        self._create_scrollable_text(parent, sql_content)
