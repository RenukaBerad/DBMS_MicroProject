# FACULTY DEMO & DBMS VIVA GUIDE
## Internal Marks Management System (Python + Tkinter + PostgreSQL)

This guide provides a step-by-step presentation script and viva preparation cheat-sheet for demonstrating your DBMS micro-project to your faculty evaluator.

---

## 1. 2-Minute Pre-Demo Checklist

1. Make sure PostgreSQL service is running on your machine.
2. Ensure you have executed `database/schema.sql` and `database/sample_data.sql` in pgAdmin 4.
3. Ensure your `.env` contains your local PostgreSQL password.
4. Launch the application:
   ```powershell
   python main.py
   ```
5. Check the **bottom status bar**: Verify it displays `● Connected: postgres@localhost:5432/internal_marks_db` in green.
6. Open **pgAdmin 4** in the background, with `internal_marks_db` expanded so you can switch windows and show actual stored rows when requested.

---

## 2. 10-Step Demonstration Walkthrough Script

### Step 1: System Overview & Live Dashboard
- **What to say:**
  > *"Good morning Professor. This is our DBMS micro-project titled 'Internal Marks Management System'. It is a native desktop application built with Python Tkinter and backed by a normalized PostgreSQL database. The dashboard currently displays live statistics calculated from PostgreSQL queries."*
- **What to show:**
  - Point to KPI cards: Total Students (8), Total Subjects (5), Marks Records (24), Evaluated Students (7), Pending Students (1), and Overall Average (79.23%).
  - Point out that **Vikram Malhotra (Roll 108)** intentionally has 0 marks records to test `LEFT JOIN` and empty-state handling.
  - Click **⟳ Refresh Dashboard** to show live query re-execution.

---

### Step 2: Student Management & Uniqueness Constraint
- **What to say:**
  > *"Next, we demonstrate the STUDENT strong entity. In addition to standard CRUD operations, our schema enforces that roll numbers must be unique within a class and division."*
- **What to show:**
  1. Click **👨‍🎓 Students** in the sidebar.
  2. In the search box, type `Sharma` and click **Search**. Show how the table filters dynamically via parameterized SQL. Click **Clear**.
  3. Select student **Aarav Sharma (ID: 1)** from the table: Notice the form on the left auto-populates.
  4. Attempt to add a duplicate student with the same class, division, and roll number:
     - Name: `Duplicate Test`
     - Roll: `101`
     - Class: `TE-COMP`
     - Div: `A`
     - Click **Save Student**.
  5. **Show the Result:** A warning dialog pops up: *"A student with this Roll Number already exists in the same Class and Division."*
     *(Explain to the faculty that this is enforced by PostgreSQL's `CONSTRAINT uq_student_roll UNIQUE (class_name, division, roll_no)`).*

---

### Step 3: Subject Management & Constraint Protection
- **What to say:**
  > *"Here we manage the SUBJECT strong entity. Maximum marks must strictly be a positive integer, enforced by both Python and a PostgreSQL CHECK constraint."*
- **What to show:**
  1. Click **📚 Subjects** in the sidebar.
  2. Show the existing subjects: DBMS (100), CN (100), OS (50), TOC (50), SE Lab (25).
  3. Try to add a subject with `max_marks = -10` or `0` to demonstrate rejection.
  4. Select **Database Management Systems** (which already has student scores up to 95.00). Try to lower its Max Marks to `50` and click **Update Selected**.
  5. **Show the Result:** An error message explains: *"Cannot reduce Maximum Marks to 50 because existing marks for this subject reach 95.0."*
     *(Explain that this is guarded by a PostgreSQL trigger `trg_check_subject_max_marks`).*

---

### Step 4: Marks Entry & Cross-Table Trigger Validation
- **What to say:**
  > *"This is the MARKS associative entity, which resolves the Many-to-Many relationship between Student and Subject."*
- **What to show:**
  1. Click **📝 Marks Entry** in the sidebar.
  2. Select **Vikram Malhotra** from the student dropdown.
  3. Select **Theory of Computation (Max: 50)** from the subject dropdown. Notice the dynamic hint: *"Subject maximum: 50 marks"*.
  4. Enter `55` in **Marks Obtained** and click **Save Marks Record**.
  5. **Show the Result:** The system rejects it: *"Invalid marks: Obtained score (55.0) exceeds the maximum marks (50.0) for Theory of Computation."*
     *(Explain that a PostgreSQL PL/pgSQL BEFORE INSERT trigger `check_marks_within_max()` enforces this).*
  5. Change the score to `42.5` and click **Save Marks Record**. Show the record appear in the table with percentage automatically computed.

---

### Step 5: Duplicate Marks Prevention
- **What to say:**
  > *"Each student should have at most one marks entry per subject."*
- **What to show:**
  1. With Vikram Malhotra and TOC still selected, click **Save Marks Record** again.
  2. **Show the Result:** Rejection message: *"A marks record already exists for this Student and Subject."*
     *(Enforced by PostgreSQL `CONSTRAINT uq_student_subject UNIQUE (student_id, subject_id)`).*

---

### Step 6: Student Marksheet & Denominator Rule
- **What to say:**
  > *"In Results & Performance, we generate individual student marksheets. The overall percentage is strictly computed across evaluated subjects only, avoiding artificial skew from unevaluated subjects."*
- **What to show:**
  1. Click **🎯 Results & Performance** in the sidebar.
  2. Select **Aarav Sharma** and click **Generate Marksheet**.
  3. Show the table with all 5 subjects, obtained marks, max marks, and percentages.
  4. Point to the green summary card at the bottom:
     `Subjects Evaluated: 5 | Total Marks: 276.00 / 325 | Overall Percentage: 84.92%`
  5. Select **Vikram Malhotra** (who only has 1 marks record) to demonstrate that the percentage denominator is correctly based on recorded subjects (1 subject, denominator 50).
  6. Click **Export CSV** to demonstrate exporting the marksheet.

---

### Step 7: Subject-wise Performance Analytics
- **What to say:**
  > *"Under the Subject Performance tab, we run live aggregate queries in PostgreSQL to analyze course-wide score distribution."*
- **What to show:**
  1. Switch to the **📈 Subject Performance** tab inside Results.
  2. Select **Database Management Systems** and click **Analyze Performance**.
  3. Show the metric tiles: Evaluated Students (7), Average Marks (80.21), Highest Marks (95.00), Lowest Marks (55.00), Average Percentage (80.21%).
  4. Show the student ranking table sorted by marks obtained in descending order.

---

### Step 8: SQL Analytical Reports
- **What to say:**
  > *"We have implemented a dedicated Reports section demonstrating essential SQL clauses."*
- **What to show:**
  1. Click **📑 SQL Reports** in the sidebar.
  2. Demonstrate:
     - **Report 1 (Student-wise Marks Ledger):** 3-table `INNER JOIN` across student, subject, and marks with calculated percentage. Filter by Class `TE-COMP` and Division `A`.
     - **Report 2 (Subject-wise Performance):** Shows `COUNT`, `AVG`, `MAX`, `MIN`, and `GROUP BY subject_name`.
     - **Report 3 (Class & Division Summary):** Shows `GROUP BY class_name, division` with `COUNT(DISTINCT student_id)` to prevent double-counting students.
     - **Report 4 (Students with No Marks):** Demonstrates `LEFT JOIN` and `WHERE marks.marks_id IS NULL`.
  3. Click **📥 Export CSV** to show that any active report can be exported.

---

### Step 9: Referential Integrity Protection (`ON DELETE RESTRICT`)
- **What to say:**
  > *"To protect against accidental data loss, our foreign keys use ON DELETE RESTRICT instead of silently deleting marks."*
- **What to show:**
  1. Go to **👨‍🎓 Students**. Select **Aarav Sharma** (who has marks records).
  2. Click **Delete Selected** and confirm the dialog.
  3. **Show the Result:** The action is blocked with an informative dialog:
     *"Cannot delete or update student because associated marks records exist. Remove student marks first."*
     *(Explain that this enforces data safety and prevents orphaned child records).*

---

### Step 10: Live pgAdmin 4 Verification
- **What to say:**
  > *"To verify that the application is truly persisting data in PostgreSQL and not using in-memory mock data, here is our live database in pgAdmin 4."*
- **What to show:**
  1. Switch to pgAdmin 4.
  2. Open the Query Tool on `internal_marks_db`.
  3. Run:
     ```sql
     SELECT * FROM student ORDER BY student_id DESC LIMIT 3;
     SELECT * FROM marks ORDER BY marks_id DESC LIMIT 3;
     ```
  4. Point out the records created during the demo.

---

## 3. High-Scoring Viva Questions & Answers

### Q1: Why is `marks` an associative entity?
> **Answer:** *"Student and Subject have a Many-to-Many ($M:N$) relationship—one student takes many subjects, and one subject has many students. In relational database theory, an M:N relationship cannot be implemented directly without introducing repeating groups or severe redundancy. Therefore, we decompose it into two 1:N relationships using the associative entity `marks`, which carries the foreign keys `student_id` and `subject_id` alongside the relationship attribute `marks_obtained`."*

---

### Q2: Why did you use a PostgreSQL Trigger instead of a CHECK constraint for marks validation?
> **Answer:** *"A standard SQL `CHECK` constraint can only evaluate column values within the same row of the same table (e.g., `CHECK (marks_obtained >= 0)`). It cannot perform a cross-table lookup to compare `marks.marks_obtained` against `subject.max_marks`. Therefore, we used a PostgreSQL PL/pgSQL `BEFORE INSERT OR UPDATE` trigger function (`check_marks_within_max()`) to perform the join lookup and raise an exception if the score exceeds the subject maximum."*

---

### Q3: What level of normalization does your database achieve?
> **Answer:** *"Our database is normalized up to **Third Normal Form (3NF)** and **Boyce-Codd Normal Form (BCNF)**:
> - **1NF:** All attribute values are atomic, and there are no repeating groups.
> - **2NF:** It is in 1NF, and all non-prime attributes are fully functionally dependent on their primary keys (eliminating partial dependencies).
> - **3NF:** It is in 2NF, and there are no transitive functional dependencies ($X \rightarrow Y$ where neither $X$ is a superkey nor $Y$ is prime).
> Decomposing into `student`, `subject`, and `marks` completely eliminates insertion, update, and deletion anomalies."*

---

### Q4: Why did you choose `ON DELETE RESTRICT` over `CASCADE`?
> **Answer:** *"In an academic grading system, marks are official, permanent assessment records. Using `CASCADE` would silently delete all historical marks if a student or course is accidentally deleted. `ON DELETE RESTRICT` halts the deletion transaction and enforces that associated marks records must be reviewed and removed deliberately first."*

---

### Q5: How do you prevent SQL Injection in your desktop app?
> **Answer:** *"We use parameterized SQL queries exclusively throughout our service layer using `%s` placeholders. User input is transmitted separately from the SQL statement through the database driver, ensuring that malicious input is treated purely as literal data and never parsed as executable SQL commands."*

---

### Q6: How do you avoid double-counting in multi-table aggregate queries?
> **Answer:** *"When joining `student` and `marks`, each student row multiplies by the number of marks records they have. If we run `COUNT(s.student_id)` in a class summary query, it would overcount the number of students. To prevent this Cartesian product distortion, we use `COUNT(DISTINCT s.student_id)`."*
