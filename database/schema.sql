-- ============================================================================
-- DBMS MICRO-PROJECT: INTERNAL MARKS MANAGEMENT SYSTEM
-- Relational Database Schema Definition (PostgreSQL)
-- ============================================================================
-- Conceptual Entities:
--   1. STUDENT  (Strong Entity)
--   2. SUBJECT  (Strong Entity)
--   3. MARKS    (Associative Entity resolving M:N relationship between Student & Subject)
--
-- Relationships:
--   - STUDENT (1) : (M) MARKS   [Foreign Key: student_id]
--   - SUBJECT (1) : (M) MARKS   [Foreign Key: subject_id]
--   - STUDENT (M) : (N) SUBJECT [Through MARKS associative table]
-- ============================================================================

-- Clean up existing objects if re-running script (reverse dependency order)
DROP TRIGGER IF EXISTS trg_check_marks_before_insert_or_update ON marks;
DROP FUNCTION IF EXISTS check_marks_within_max();
DROP TRIGGER IF EXISTS trg_check_subject_max_marks ON subject;
DROP FUNCTION IF EXISTS check_subject_max_marks_update();

DROP TABLE IF EXISTS marks CASCADE;
DROP TABLE IF EXISTS subject CASCADE;
DROP TABLE IF EXISTS student CASCADE;

-- ----------------------------------------------------------------------------
-- 1. TABLE: student
-- ----------------------------------------------------------------------------
-- Maps to ER Entity: STUDENT
-- Attributes:
--   student_id : Primary Key (Surrogate key using SERIAL)
--   name       : Student full name (NOT NULL)
--   roll_no    : Roll number allocated within class/division (NOT NULL)
--   class_name : Class/Grade (mapped from ER attribute 'class' to avoid SQL reserved keyword)
--   division   : Section/Division (NOT NULL)
-- Integrity:
--   UNIQUE(class_name, division, roll_no) prevents duplicate roll numbers in the same division.
-- ----------------------------------------------------------------------------
CREATE TABLE student (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(20) NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    division VARCHAR(10) NOT NULL,
    CONSTRAINT uq_student_roll UNIQUE (class_name, division, roll_no)
);

COMMENT ON TABLE student IS 'Stores student personal and academic identification details';
COMMENT ON COLUMN student.student_id IS 'Unique primary key identifier for each student';
COMMENT ON COLUMN student.class_name IS 'Physical column mapped to conceptual ER attribute class';
COMMENT ON CONSTRAINT uq_student_roll ON student IS 'Ensures roll number is unique within a specific class and division';

-- ----------------------------------------------------------------------------
-- 2. TABLE: subject
-- ----------------------------------------------------------------------------
-- Maps to ER Entity: SUBJECT
-- Attributes:
--   subject_id   : Primary Key (Surrogate key using SERIAL)
--   subject_name : Subject title (NOT NULL, UNIQUE)
--   max_marks    : Maximum possible marks for the internal assessment (CHECK > 0)
-- ----------------------------------------------------------------------------
CREATE TABLE subject (
    subject_id SERIAL PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL UNIQUE,
    max_marks INT NOT NULL CHECK (max_marks > 0)
);

COMMENT ON TABLE subject IS 'Stores course subjects and their maximum internal assessment marks';
COMMENT ON COLUMN subject.subject_id IS 'Unique primary key identifier for each subject';
COMMENT ON COLUMN subject.max_marks IS 'Maximum marks allowed for this subject; must be strictly positive';

-- ----------------------------------------------------------------------------
-- 3. TABLE: marks
-- ----------------------------------------------------------------------------
-- Maps to ER Associative Entity: MARKS
-- Resolves M:N relationship between STUDENT and SUBJECT.
-- Attributes:
--   marks_id       : Primary Key
--   student_id     : Foreign Key referencing student(student_id)
--   subject_id     : Foreign Key referencing subject(subject_id)
--   marks_obtained : Assessment score achieved (CHECK >= 0)
-- Integrity:
--   UNIQUE(student_id, subject_id) ensures a student has exactly one marks record per subject.
--   ON DELETE RESTRICT prevents accidental deletion of student or subject when marks exist.
-- ----------------------------------------------------------------------------
CREATE TABLE marks (
    marks_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    marks_obtained NUMERIC(5, 2) NOT NULL CHECK (marks_obtained >= 0),
    CONSTRAINT fk_marks_student FOREIGN KEY (student_id)
        REFERENCES student(student_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT uq_student_subject UNIQUE (student_id, subject_id)
);

COMMENT ON TABLE marks IS 'Associative table recording marks scored by students in subjects';
COMMENT ON COLUMN marks.marks_id IS 'Primary key identifier for marks transaction';
COMMENT ON COLUMN marks.marks_obtained IS 'Internal marks scored; enforced <= subject.max_marks by trigger';
COMMENT ON CONSTRAINT fk_marks_student ON marks IS 'Referential integrity to student table with RESTRICT delete';
COMMENT ON CONSTRAINT fk_marks_subject ON marks IS 'Referential integrity to subject table with RESTRICT delete';
COMMENT ON CONSTRAINT uq_student_subject ON marks IS 'Prevents duplicate marks entry for same student and subject';

-- ----------------------------------------------------------------------------
-- 4. DATABASE-LEVEL BUSINESS INTEGRITY TRIGGERS
-- ----------------------------------------------------------------------------
-- Trigger Function 1: check_marks_within_max()
-- Enforces: marks.marks_obtained <= subject.max_marks
-- Standard SQL CHECK cannot reference columns from another table;
-- a BEFORE INSERT/UPDATE trigger enforces cross-table constraint in PostgreSQL.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_marks_within_max()
RETURNS TRIGGER AS $$
DECLARE
    sub_max INT;
    sub_title VARCHAR(100);
BEGIN
    SELECT max_marks, subject_name INTO sub_max, sub_title
    FROM subject
    WHERE subject_id = NEW.subject_id;

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

-- ----------------------------------------------------------------------------
-- Trigger Function 2: check_subject_max_marks_update()
-- Enforces: If an administrator reduces a subject's max_marks, existing marks
-- must not exceed the newly proposed max_marks.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_subject_max_marks_update()
RETURNS TRIGGER AS $$
DECLARE
    highest_existing NUMERIC;
BEGIN
    SELECT MAX(marks_obtained) INTO highest_existing
    FROM marks
    WHERE subject_id = NEW.subject_id;

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

-- ----------------------------------------------------------------------------
-- 5. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
-- Optimize joins and filter queries across class, division, and foreign keys
CREATE INDEX idx_student_class_div ON student(class_name, division);
CREATE INDEX idx_student_name ON student(name);
CREATE INDEX idx_marks_student ON marks(student_id);
CREATE INDEX idx_marks_subject ON marks(subject_id);

-- Verify schema creation summary
SELECT 'Schema initialized successfully. Tables: student, subject, marks.' AS status;
