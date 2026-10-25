-- ============================================================================
-- DBMS MICRO-PROJECT: INTERNAL MARKS MANAGEMENT SYSTEM
-- Coherent Demonstration Dataset (PostgreSQL)
-- ============================================================================
-- Instructions:
--   Run this script after executing schema.sql.
--   It populates:
--     - 8 Students across TE-COMP (Div A, Div B) and BE-COMP (Div A)
--     - 5 Subjects with varied maximum marks (100, 50, 25)
--     - 20+ Marks records spanning high, mid, low, and edge values
--     - 1 Student (Roll 108 - "Vikram Malhotra") intentionally has NO marks
--       to test LEFT JOIN queries and "Students with no marks" reports.
-- ============================================================================

-- Clean existing data safely (maintaining foreign key order)
-- Uncomment the following 3 lines if you wish to reset sample data:
-- TRUNCATE TABLE marks RESTART IDENTITY CASCADE;
-- TRUNCATE TABLE subject RESTART IDENTITY CASCADE;
-- TRUNCATE TABLE student RESTART IDENTITY CASCADE;

-- ----------------------------------------------------------------------------
-- 1. INSERT STUDENTS
-- ----------------------------------------------------------------------------
INSERT INTO student (name, roll_no, class_name, division) VALUES
('Aarav Sharma',     '101', 'TE-COMP', 'A'),
('Diya Patel',       '102', 'TE-COMP', 'A'),
('Rohan Kulkarni',   '103', 'TE-COMP', 'A'),
('Ananya Deshmukh',  '104', 'TE-COMP', 'B'),
('Kabir Mehta',      '105', 'TE-COMP', 'B'),
('Sneha Joshi',      '201', 'BE-COMP', 'A'),
('Aditya Verma',     '202', 'BE-COMP', 'A'),
('Vikram Malhotra',  '108', 'TE-COMP', 'B')  -- Intentionally has NO marks!
ON CONFLICT (class_name, division, roll_no) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 2. INSERT SUBJECTS
-- ----------------------------------------------------------------------------
INSERT INTO subject (subject_name, max_marks) VALUES
('Database Management Systems', 100),
('Computer Networks',           100),
('Operating Systems',            50),
('Theory of Computation',        50),
('Software Engineering Lab',     25)
ON CONFLICT (subject_name) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3. INSERT MARKS RECORDS
-- ----------------------------------------------------------------------------
-- All marks are strictly validated <= subject.max_marks
-- 
-- Subject References:
--   Sub 1: Database Management Systems (Max: 100)
--   Sub 2: Computer Networks (Max: 100)
--   Sub 3: Operating Systems (Max: 50)
--   Sub 4: Theory of Computation (Max: 50)
--   Sub 5: Software Engineering Lab (Max: 25)
-- ----------------------------------------------------------------------------

-- Student 1: Aarav Sharma (TE-COMP Div A)
INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES
(1, 1, 88.50), -- DBMS (Max 100)
(1, 2, 79.00), -- CN (Max 100)
(1, 3, 44.00), -- OS (Max 50)
(1, 4, 41.50), -- TOC (Max 50)
(1, 5, 23.00)  -- SE Lab (Max 25)
ON CONFLICT (student_id, subject_id) DO NOTHING;

-- Student 2: Diya Patel (TE-COMP Div A)
INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES
(2, 1, 95.00), -- Top score in DBMS
(2, 2, 92.50),
(2, 3, 48.00),
(2, 4, 46.00),
(2, 5, 24.50)
ON CONFLICT (student_id, subject_id) DO NOTHING;

-- Student 3: Rohan Kulkarni (TE-COMP Div A)
INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES

(3, 1, 62.00),
(3, 2, 58.50),
(3, 3, 31.00),
(3, 4, 28.00),
(3, 5, 18.00)
ON CONFLICT (student_id, subject_id) DO NOTHING;

-- Student 4: Ananya Deshmukh (TE-COMP Div B)
INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES
(4, 1, 84.00),
(4, 2, 81.00),
(4, 3, 42.50),
(4, 4, 39.00),
(4, 5, 22.00)
ON CONFLICT (student_id, subject_id) DO NOTHING;

-- Student 5: Kabir Mehta (TE-COMP Div B)
INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES
(5, 1, 71.50),
(5, 2, 65.00),
(5, 3, 35.00),
(5, 4, 30.50),
(5, 5, 19.50)
ON CONFLICT (student_id, subject_id) DO NOTHING;

-- Student 6: Sneha Joshi (BE-COMP Div A)
INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES
(6, 1, 91.00),
(6, 2, 89.00),
(6, 3, 47.00),
(6, 5, 24.00)
ON CONFLICT (student_id, subject_id) DO NOTHING;

-- Student 7: Aditya Verma (BE-COMP Div A)
INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES
(7, 1, 55.00),
(7, 2, 60.00),
(7, 3, 27.50),
(7, 5, 17.00)
ON CONFLICT (student_id, subject_id) DO NOTHING;

-- Note: Student 8 (Vikram Malhotra) intentionally left without marks records
-- for demonstrations of outer joins and empty state handling.

-- Display confirmation count
SELECT 
    (SELECT COUNT(*) FROM student) AS total_students,
    (SELECT COUNT(*) FROM subject) AS total_subjects,
    (SELECT COUNT(*) FROM marks)   AS total_marks_records;
