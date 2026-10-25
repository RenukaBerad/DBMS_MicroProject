# ACADEMIC DBMS MICRO-PROJECT REPORT
## Title: Internal Marks Management System
**Department of Computer Engineering**  
**Course:** Database Management Systems (DBMS)  
**Technology Stack:** Python 3, Tkinter (ttk), PostgreSQL, Psycopg  

---

## 1. Introduction & Problem Statement

### 1.1 Problem Statement
In conventional educational institutions, internal marks, practical test scores, and term-work assessments are predominantly recorded across fragmented spreadsheets, paper registers, or isolated files. This decentralized approach introduces significant structural and operational challenges:
1. **Data Redundancy & Inconsistency:** Student details (such as roll numbers, class, and division) are duplicated across multiple spreadsheets for different subjects, leading to update anomalies.
2. **Lack of Validation & Integrity:** Spreadsheets do not enforce strict cross-field business constraints (e.g., preventing scores from exceeding a subject's maximum marks, or ensuring roll numbers are unique within a class division).
3. **Difficulty in Cross-Subject Reporting:** Generating student-wise overall percentage summaries or subject-wise score distributions requires complex, error-prone manual formulas.
4. **Accidental Deletions:** In unnormalized systems, deleting a course or student record can inadvertently erase historical marks or orphan assessment records.

### 1.2 Objectives
The primary objective of this micro-project is to design, normalize, and implement a robust, relational desktop application backed by **PostgreSQL** to manage student academic records, curriculum subjects, and internal assessment marks.

Key goals:
- Transform conceptual ER models into a normalized relational schema (up to **3NF / BCNF**).
- Enforce database-level integrity via **Primary Keys**, **Foreign Keys (`ON DELETE RESTRICT`)**, **UNIQUE constraints**, **CHECK constraints**, and **PostgreSQL PL/pgSQL Triggers**.
- Provide a clean, intuitive Python Tkinter desktop GUI for CRUD operations and live analytical reporting.
- Implement parameterized SQL queries to prevent SQL injection vulnerabilities and guarantee transactional reliability (`COMMIT` / `ROLLBACK`).

### 1.3 Scope
The scope encompasses:
- Managing student profiles within classes and divisions.
- Managing curriculum subjects and their maximum marks.
- Recording, updating, and filtering marks scored by students across subjects.
- Generating live marksheets and analytical performance reports.
- Resolving the Many-to-Many ($M:N$) relationship between Students and Subjects via an associative entity (`marks`).

---

## 2. Hardware and Software Requirements

### 2.1 Hardware Requirements
- **Processor:** Intel Core i3 / AMD Ryzen 3 or higher.
- **RAM:** Minimum 4 GB (8 GB recommended for concurrent PostgreSQL and pgAdmin usage).
- **Storage:** 500 MB free hard disk space.
- **Display:** Minimum resolution 1024x768 (1280x768 recommended).

### 2.2 Software Requirements
- **Operating System:** Windows 10 / Windows 11 (or Linux / macOS).
- **Programming Language:** Python 3.10+ (standard distribution with Tkinter 8.6).
- **Database Management System:** PostgreSQL 12.0 or higher.
- **Database Administration GUI:** pgAdmin 4.
- **Database Drivers:** `psycopg2-binary` (or `psycopg` v3).
- **Environment Management:** `python-dotenv`.

---

## 3. Entity-Relationship (ER) Modeling & Conceptual Design

### 3.1 Entity Identification & Classification
The domain comprises three primary entities:

1. **STUDENT (Strong Entity):**
   - Independent real-world entity representing enrolled learners.
   - Primary Identifier: `student_id`.
   - Attributes: `name`, `roll_no`, `class` (mapped to `class_name`), `division`.

2. **SUBJECT (Strong Entity):**
   - Independent entity representing academic curriculum courses.
   - Primary Identifier: `subject_id`.
   - Attributes: `subject_name`, `max_marks`.

3. **MARKS (Associative Entity):**
   - Resolves the Many-to-Many ($M:N$) relationship between `STUDENT` and `SUBJECT`.
   - Primary Identifier: `marks_id`.
   - Foreign Keys: `student_id` (references STUDENT), `subject_id` (references SUBJECT).
   - Relationship Attribute: `marks_obtained`.

### 3.2 Cardinality & Structural Constraints
- **STUDENT to MARKS (1 : N):** One student may have zero, one, or multiple marks records (one for each evaluated subject). Each marks record belongs to exactly one student.
- **SUBJECT to MARKS (1 : N):** One subject may have zero, one, or multiple marks records (from enrolled students). Each marks record pertains to exactly one subject.
- **STUDENT to SUBJECT (M : N):** A student takes multiple subjects; a subject is taken by multiple students. The associative entity `MARKS` resolves this into two binary 1:N relationships.

```
+------------------+                    +------------------+
|     STUDENT      | 1                N |      MARKS       |
|------------------|--------------------|------------------|
| PK  student_id   |<-------+           | PK  marks_id     |
|     name         |        |           | FK  student_id   |----+
|     roll_no      |        +-----------| FK  subject_id   |    |
|     class_name   |                    |     marks_obt    |    |
|     division     |                    +------------------+    |
+------------------+                                            |
                                                                |
                                        +------------------+    |
                                        |     SUBJECT      | 1  |
                                        |------------------|    |
                                        | PK  subject_id   |<---+
                                        |     subject_name |
                                        |     max_marks    |
                                        +------------------+
```

---

## 4. Relational Schema & Data Dictionary

### 4.1 Physical Schema Definition

#### Table 1: `student`
| Column Name | Physical Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `student_id` | `SERIAL` | `PRIMARY KEY` | Unique surrogate identifier for student |
| `name` | `VARCHAR(100)` | `NOT NULL` | Student full legal name |
| `roll_no` | `VARCHAR(20)` | `NOT NULL` | Roll number allocated within division |
| `class_name` | `VARCHAR(50)` | `NOT NULL` | Academic class / grade (e.g. TE-COMP) |
| `division` | `VARCHAR(10)` | `NOT NULL` | Section / Division (e.g. A, B) |
| *Composite* | — | `UNIQUE (class_name, division, roll_no)` | Prevents duplicate roll numbers per division |

#### Table 2: `subject`
| Column Name | Physical Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `subject_id` | `SERIAL` | `PRIMARY KEY` | Unique surrogate identifier for subject |
| `subject_name` | `VARCHAR(100)` | `NOT NULL, UNIQUE` | Official title of curriculum subject |
| `max_marks` | `INT` | `NOT NULL, CHECK (max_marks > 0)` | Maximum achievable score |

#### Table 3: `marks`
| Column Name | Physical Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `marks_id` | `SERIAL` | `PRIMARY KEY` | Transaction identifier for assessment entry |
| `student_id` | `INT` | `NOT NULL, FK -> student(student_id)` | Referential link to student (`ON DELETE RESTRICT`) |
| `subject_id` | `INT` | `NOT NULL, FK -> subject(subject_id)` | Referential link to subject (`ON DELETE RESTRICT`) |
| `marks_obtained` | `NUMERIC(5,2)` | `NOT NULL, CHECK (marks_obtained >= 0)` | Assessment score achieved |
| *Composite* | — | `UNIQUE (student_id, subject_id)` | Enforces at most one mark per student-subject |

---

## 5. Database Normalization Analysis

### 5.1 Unnormalized Form (UNF)
In an unnormalized paper ledger:
$$\text{LEDGER}(\underline{\text{roll\_no}}, \text{class}, \text{division}, \text{name}, \{\text{subject\_name}, \text{max\_marks}, \text{marks\_obtained}\})$$
*Anomalies:* Contains repeating multi-valued groups for subjects and marks.

### 5.2 First Normal Form (1NF)
Eliminate repeating groups by ensuring all attribute domains are atomic.
$$\text{GRADE\_1NF}(\underline{\text{roll\_no}, \text{class}, \text{division}, \text{subject\_name}}, \text{name}, \text{max\_marks}, \text{marks\_obtained})$$
*Composite Candidate Key:* $(\text{class}, \text{division}, \text{roll\_no}, \text{subject\_name})$.

*Anomalies in 1NF:*
- **Redundancy:** Student name is duplicated for every subject enrolled.
- **Insertion Anomaly:** Cannot record a new subject until at least one student enrolls and scores marks.
- **Deletion Anomaly:** Deleting the only student enrolled in a subject deletes the subject metadata itself.
- **Partial Functional Dependencies:**
  - $(\text{class}, \text{division}, \text{roll\_no}) \rightarrow \text{name}$ *(Depends on part of the candidate key)*
  - $\text{subject\_name} \rightarrow \text{max\_marks}$ *(Depends on part of the candidate key)*

### 5.3 Second Normal Form (2NF)
A relation is in 2NF if it is in 1NF and no non-prime attribute is partially dependent on any candidate key.
We decompose into three relations:
1. $\text{STUDENT}(\underline{\text{student\_id}}, \text{name}, \text{roll\_no}, \text{class\_name}, \text{division})$
2. $\text{SUBJECT}(\underline{\text{subject\_id}}, \text{subject\_name}, \text{max\_marks})$
3. $\text{MARKS}(\underline{\text{marks\_id}}, \text{student\_id}, \text{subject\_id}, \text{marks\_obtained})$

Now, every non-prime attribute is fully dependent on its respective primary key.

### 5.4 Third Normal Form (3NF)
A relation is in 3NF if it is in 2NF and no transitive functional dependency exists between non-prime attributes ($X \rightarrow Y$ implies $X$ is a superkey or $Y$ is a prime attribute).
- In `student`, `student_id` determines all descriptive attributes; no non-prime attribute determines another non-prime attribute.
- In `subject`, `subject_id` uniquely determines `subject_name` and `max_marks`.
- In `marks`, `marks_id` determines `student_id`, `subject_id`, and `marks_obtained`.

**Conclusion:** The database schema is fully in **3NF** (and **BCNF**).

---

## 6. Business Integrity & PostgreSQL Triggers

### 6.1 Cross-Table Marks Validation Trigger
Standard SQL column `CHECK` constraints cannot reference values in external tables. To ensure in PostgreSQL that $0 \le \text{marks\_obtained} \le \text{subject.max\_marks}$, a PL/pgSQL trigger was implemented:

```sql
CREATE OR REPLACE FUNCTION check_marks_within_max()
RETURNS TRIGGER AS $$
DECLARE
    sub_max INT;
    sub_title VARCHAR(100);
BEGIN
    SELECT max_marks, subject_name INTO sub_max, sub_title
    FROM subject WHERE subject_id = NEW.subject_id;

    IF sub_max IS NULL THEN
        RAISE EXCEPTION 'Referenced Subject ID % does not exist.', NEW.subject_id;
    END IF;

    IF NEW.marks_obtained > sub_max THEN
        RAISE EXCEPTION 'Invalid marks: Obtained score (%) exceeds maximum marks (%) for subject "%".',
            NEW.marks_obtained, sub_max, sub_title;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_marks_before_insert_or_update
BEFORE INSERT OR UPDATE ON marks
FOR EACH ROW
EXECUTE FUNCTION check_marks_within_max();
```

### 6.2 Max Marks Reduction Protection Trigger
Prevents an administrator from reducing a subject's `max_marks` if existing marks records for that subject already exceed the proposed lower maximum:

```sql
CREATE OR REPLACE FUNCTION check_subject_max_marks_update()
RETURNS TRIGGER AS $$
DECLARE
    highest_existing NUMERIC;
BEGIN
    SELECT MAX(marks_obtained) INTO highest_existing
    FROM marks WHERE subject_id = NEW.subject_id;

    IF highest_existing IS NOT NULL AND NEW.max_marks < highest_existing THEN
        RAISE EXCEPTION 'Cannot reduce max_marks to % because existing marks for subject "%" reach %.',
            NEW.max_marks, NEW.subject_name, highest_existing;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_subject_max_marks
BEFORE UPDATE OF max_marks ON subject
FOR EACH ROW
EXECUTE FUNCTION check_subject_max_marks_update();
```

---

## 7. Application Features & Implementation

### 7.1 Dashboard Home
- Real-time KPI summary computed dynamically via live SQL queries:
  - Total students, Total subjects, Total marks records.
  - Students with at least 1 marks record vs. Students with 0 marks records.
  - Overall average percentage across recorded evaluations.
- Recent marks transaction ledger.
- Offline status detection and alert banner.

### 7.2 Student Management
- Full CRUD interface with `ttk.Treeview`.
- Multi-field search across ID, Name, Roll No, Class, and Division.
- Duplicate prevention using `UNIQUE (class_name, division, roll_no)`.
- Foreign key protection on deletion (`ON DELETE RESTRICT`).

### 7.3 Subject Management
- Subject registration with name and positive `max_marks`.
- Protection against invalid reductions in maximum marks.
- Associated marks record count display.

### 7.4 Marks Entry & Management
- Associative record entry linking students and subjects via comboboxes.
- Real-time display of subject max marks hint.
- Automatic calculation of subject percentage:
  $$\text{Percentage} = \text{ROUND}\left(\frac{\text{marks\_obtained}}{\text{max\_marks}} \times 100.0, 2\right)$$
- Multi-parameter filtering by Class, Division, and Subject.

### 7.5 Academic Results & Performance Analytics
- **Student Marksheet:** Shows student info, subject breakdown, and summary.
  - *Denominator Rule:* Overall percentage is calculated strictly across evaluated subjects:
    $$\text{Overall } \% = \frac{\sum \text{marks\_obtained}}{\sum \text{max\_marks for recorded subjects}} \times 100.0$$
- **Subject Analytics:** Aggregate statistics for any subject (Count, Average, Min, Max, Average %).
- **CSV Export:** Capability to export marksheets and performance data to `.csv` files.

### 7.6 Dedicated SQL Analytical Reports
1. **Report 1 (Student-wise Marks Report):** 3-table `INNER JOIN` with calculated columns and sorting.
2. **Report 2 (Subject-wise Performance):** `GROUP BY` with aggregate functions (`COUNT`, `AVG`, `MAX`, `MIN`).
3. **Report 3 (Class & Division Summary):** Uses `COUNT(DISTINCT student_id)` to eliminate Cartesian product overcounting.
4. **Report 4 (Unevaluated Students):** Uses `LEFT OUTER JOIN` and `WHERE marks.marks_id IS NULL`.

---

## 8. Test Execution & Verification Results

### 8.1 Automated Unit & Integration Tests
The project includes automated tests in `tests/`:
- `tests/test_validation.py` (Input validation, length boundaries, configuration masking)
- `tests/test_calculations.py` (Percentages, denominator rules, zero-division guards)
- `tests/test_database_operations.py` (Parameterized query formatting, transaction rollback)

**Execution Command:**
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

**Test Results:**
```
Ran 23 tests in 4.115s
OK
```

All 23 test cases passed successfully.

### 8.2 Database Constraint Tests (pgAdmin Verification)
| Test Scenario | Executed Operation | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- |
| **Unique Roll No** | Insert duplicate roll number in same class/div | Error: duplicate key violates `uq_student_roll` | Handled gracefully with user warning |
| **Negative Max Marks** | Insert subject with `max_marks = -10` | Error: violates check constraint `subject_max_marks_check` | Handled with validation message |
| **Marks > Max Marks** | Insert marks of 105 in 100-mark subject | Error from `check_marks_within_max()` trigger | Trigger fired, transaction rolled back |
| **Duplicate Marks** | Insert second marks record for same (student, subject) | Error: violates `uq_student_subject` | Blocked with "Record already exists" |
| **Delete With Marks** | Delete student with existing marks records | Error: violates `fk_marks_student` (`ON DELETE RESTRICT`) | Blocked with explanation to remove marks first |

---

## 9. Application Screenshots Section

*(Insert screenshots of your running application here for report submission)*

1. **Dashboard Home:** Showing live KPI tiles and recent marks records.
2. **Student Management Screen:** Showing student form, search filter, and treeview.
3. **Subject Management Screen:** Showing curriculum list and max marks validation.
4. **Marks Entry Screen:** Showing combobox selection, live max marks reminder, and treeview.
5. **Student Marksheet:** Showing individual student statement of marks and calculated overall percentage.
6. **Subject Performance Analytics:** Showing score distributions and metric cards.
7. **SQL Analytical Reports:** Showing 3-table join report and CSV export option.
8. **pgAdmin 4 Verification:** Showing tables and live rows in pgAdmin query tool.

---

## 10. Conclusion & Future Scope

### 10.1 Conclusion
The **Internal Marks Management System** successfully addresses the pitfalls of spreadsheet-based mark recording by establishing a robust, normalized relational database backed by PostgreSQL. The system cleanly resolves the Many-to-Many relationship through the associative entity `marks`, enforces data integrity at both the database level (via constraints and triggers) and the application level (via Python validation), and provides responsive analytical reports and marksheets through live SQL queries.

### 10.2 Future Scope
- **Role-Based Access Control (RBAC):** Introducing teacher and student login authentication.
- **Batch CSV Import:** Allowing faculty to bulk-import marks from standardized exam sheets.
- **PDF Report Card Generation:** Direct compilation of university-standard marksheets to PDF.
- **Grade Point Average (GPA) & SGPA:** Automated credit-based grading calculations.
