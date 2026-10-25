# Internal Marks Management System
### Python 3 + Tkinter + PostgreSQL DBMS Micro-Project

A complete, production-grade desktop database application built for a college Database Management Systems (DBMS) micro-project and viva demonstration.

---

## 1. Project Overview & Architecture

- **Application Type:** Native Desktop Application (Python + Tkinter / ttk).
- **Relational Database:** PostgreSQL (12+ recommended).
- **Python Database Driver:** `psycopg2-binary` / `psycopg3` (supports both seamlessly).
- **Architecture:** Clean 3-Tier Layered Architecture:
  - **Presentation Layer (`gui/`):** Tkinter frames, dashboard cards, custom ttk styles, input validation, and treeviews.
  - **Service Layer (`services/`):** Business logic, parameterization, and aggregate queries.
  - **Data Access Layer (`database.py`):** PostgreSQL connection management, transaction commit/rollback, and constraint error translation.
  - **Database Layer (`database/`):** PostgreSQL DDL schema, foreign key restrictions, triggers, and demonstration dataset.

---

## 2. Relational Schema & ER Mapping

The database schema implements the 3 core entities:

1. **`student`** (Strong Entity):
   - `student_id SERIAL PRIMARY KEY`
   - `name VARCHAR(100) NOT NULL`
   - `roll_no VARCHAR(20) NOT NULL`
   - `class_name VARCHAR(50) NOT NULL` (Mapped from conceptual ER attribute `class` to avoid SQL keyword conflicts)
   - `division VARCHAR(10) NOT NULL`
   - `CONSTRAINT uq_student_roll UNIQUE (class_name, division, roll_no)`

2. **`subject`** (Strong Entity):
   - `subject_id SERIAL PRIMARY KEY`
   - `subject_name VARCHAR(100) NOT NULL UNIQUE`
   - `max_marks INT NOT NULL CHECK (max_marks > 0)`

3. **`marks`** (Associative Entity resolving M:N relationship):
   - `marks_id SERIAL PRIMARY KEY`
   - `student_id INT NOT NULL REFERENCES student(student_id) ON DELETE RESTRICT ON UPDATE CASCADE`
   - `subject_id INT NOT NULL REFERENCES subject(subject_id) ON DELETE RESTRICT ON UPDATE CASCADE`
   - `marks_obtained NUMERIC(5, 2) NOT NULL CHECK (marks_obtained >= 0)`
   - `CONSTRAINT uq_student_subject UNIQUE (student_id, subject_id)`
   - **PostgreSQL Trigger (`trg_check_marks_before_insert_or_update`):** Enforces cross-table check `marks_obtained <= subject.max_marks`.
   - **PostgreSQL Trigger (`trg_check_subject_max_marks`):** Prevents lowering a subject's `max_marks` below existing marks scores.

---

## 3. Prerequisites & Environment Check

Before running the application, make sure you have:
1. **Python 3.10+** installed on Windows.
2. **PostgreSQL** and **pgAdmin 4** installed locally.

---

## 4. Step-by-Step Installation & Setup (Windows PowerShell)

Open **Windows PowerShell** in this project directory (`c:\Users\Lenovo\OneDrive\Desktop\DBMS_MicroProject`):

### Step 4.1: Verify Python & Tkinter
```powershell
python --version
python -c "import tkinter; print('Tkinter available:', tkinter.TkVersion)"
```

### Step 4.2: Create and Activate Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 4.3: Install Python Dependencies
```powershell
pip install -r requirements.txt
```
*(Dependencies: `psycopg2-binary` and `python-dotenv`)*

---

## 5. PostgreSQL Database Setup via pgAdmin 4 or psql

### Step 5.1: Create the Database
Open **pgAdmin 4**:
1. Connect to your local PostgreSQL server in the left browser tree.
2. Right-click **Databases** → **Create** → **Database...**.
3. Set **Database** name to: `internal_marks_db`.
4. Click **Save**.

*(Or via psql command line:)*
```sql
CREATE DATABASE internal_marks_db;
```

### Step 5.2: Execute `database/schema.sql`
1. In pgAdmin, select `internal_marks_db`.
2. Click **Tools** → **Query Tool** (or press `Alt + Shift + Q`).
3. Click the folder icon (Open File) and select `database/schema.sql` from your project folder.
4. Click the **Execute / Run** button (`F5`).
5. Confirm output message: `Schema initialized successfully. Tables: student, subject, marks.`

### Step 5.3: Execute `database/sample_data.sql`
1. In the Query Tool, open `database/sample_data.sql`.
2. Click **Execute / Run** (`F5`).
3. Confirm that 8 students, 5 subjects, and 24 marks records are inserted.

---

## 6. Configure Local Environment (`.env`)

Copy `.env.example` to create your local `.env` file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code or Notepad and set your local PostgreSQL credentials:

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=internal_marks_db
DB_USER=postgres
DB_PASSWORD=your_actual_postgres_password
```
> [!IMPORTANT]
> - Replace `your_actual_postgres_password` with the password you set when installing PostgreSQL.
> - Never commit your `.env` file to Git (it is already included in `.gitignore`).

---

## 7. Run Automated Tests

Run the test suite to verify validation rules, calculation logic, and database operations:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

All 23 tests should pass (`OK`).

---

## 8. Launch the Application

Launch the desktop application:

```powershell
python main.py
```

The application window will open:
- Look at the **bottom status bar**: It should show `● Connected: postgres@localhost:5432/internal_marks_db`.
- If it shows `Offline / Disconnected`, click **⚙️ DB Settings** in the bottom-left sidebar to adjust credentials, click **Test Connection**, and then **Save & Connect**.

---

## 9. How to Verify Stored Records in pgAdmin 4

To demonstrate to your professor that data is genuinely persisted in PostgreSQL:

1. In **pgAdmin 4**, expand:
   `Servers` → `PostgreSQL` → `Databases` → `internal_marks_db` → `Schemas` → `public` → `Tables`.
2. Right-click table `student` → **View/Edit Data** → **All Rows**.
3. Right-click table `subject` → **View/Edit Data** → **All Rows**.
4. Right-click table `marks` → **View/Edit Data** → **All Rows**.
5. In Query Tool, run:
   ```sql
   SELECT 
       s.roll_no, s.name, s.class_name, s.division,
       sub.subject_name, sub.max_marks, m.marks_obtained,
       ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
   FROM marks m
   JOIN student s ON m.student_id = s.student_id
   JOIN subject sub ON m.subject_id = sub.subject_id;
   ```

---

## 10. Application Feature Guide

| Section | Key Features |
| :--- | :--- |
| **📊 Dashboard** | Live KPI tiles (Total Students, Subjects, Marks Records, Evaluated Students, Pending Students, Overall Avg %) and Recent Marks ledger. |
| **👨‍🎓 Students** | Complete CRUD operations, multi-field search (ID, Name, Roll No, Class, Division), unique constraint enforcement (`class_name, division, roll_no`). |
| **📚 Subjects** | Complete CRUD operations, max marks range check, and protection preventing reduction of max marks below existing student scores. |
| **📝 Marks Entry** | Dropdowns showing formatted student profiles and subjects, real-time max marks validation, duplicate entry prevention, and score updates. |
| **🎯 Results** | **Tab 1:** Individual student marksheets with overall percentage strictly across recorded subjects. **Tab 2:** Subject score distribution (Avg, Min, Max, Count) + CSV export. |
| **📑 SQL Reports** | 4 working SQL reports with live queries, multi-parameter filters, CSV export, and SQL concept explanations. |
| **💡 DBMS Guide** | In-app viva guide with ER diagrams, 1NF → 2NF → 3NF normalization, constraint analysis, and SQL queries reference. |

---

## 11. Troubleshooting Common Issues

- **`Authentication failed for user 'postgres'`:**
  Check `DB_PASSWORD` in your `.env` file or click **⚙️ DB Settings** in the app to re-enter it.
- **`Could not connect to server: Connection refused`:**
  Verify that the Windows PostgreSQL service is running. Open PowerShell as Administrator and run: `Start-Service postgresql*`.
- **`Database 'internal_marks_db' does not exist`:**
  Create the database in pgAdmin 4 before running `database/schema.sql`.
- **`Cannot delete student/subject because marks records exist`:**
  This is the intended referential integrity rule (`ON DELETE RESTRICT`). Delete or reassign related marks records before deleting the parent record.
