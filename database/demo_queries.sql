-- ============================================================================
-- DBMS MICRO-PROJECT: INTERNAL MARKS MANAGEMENT SYSTEM
-- Demonstration SQL Queries and Viva Concept Verification
-- ============================================================================
-- This script contains standard SQL statements demonstrating fundamental
-- database concepts required for evaluation, faculty viva, and verification.
-- ============================================================================

-- ============================================================================
-- SECTION 1: BASIC DML OPERATIONS (SELECT, WHERE, ORDER BY)
-- ============================================================================

-- Query 1.1: Retrieve all registered students sorted by Class, Division, and Roll Number
SELECT 
    student_id, 
    name, 
    roll_no, 
    class_name, 
    division 
FROM student 
ORDER BY class_name ASC, division ASC, roll_no::INT ASC;

-- Query 1.2: Retrieve all subjects and their maximum marks
SELECT 
    subject_id, 
    subject_name, 
    max_marks 
FROM subject 
ORDER BY subject_id ASC;

-- Query 1.3: Search students by pattern in name or roll number (demonstrating LIKE / ILIKE)
SELECT 
    student_id, 
    name, 
    roll_no, 
    class_name, 
    division
FROM student
WHERE name ILIKE '%Sharma%' OR roll_no = '101';


-- ============================================================================
-- SECTION 2: TABLE JOINS & CALCULATED COLUMNS (INNER JOIN)
-- ============================================================================

-- Query 2.1: Complete marks ledger showing Student, Subject, and Percentage
-- Demonstrates: 3-table INNER JOIN, calculated column, rounding
SELECT 
    m.marks_id,
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
ORDER BY s.class_name, s.division, s.roll_no, sub.subject_name;


-- ============================================================================
-- SECTION 3: STUDENT-WISE RESULTS CALCULATION (REPORT 1)
-- ============================================================================

-- Query 3.1: Complete Marksheet for a single student (e.g., student_id = 1)
-- Demonstrates: Filtering by Foreign Key, Subject Details, and Subject Percentages
SELECT 
    s.student_id,
    s.name AS student_name,
    s.roll_no,
    s.class_name,
    s.division,
    sub.subject_id,
    sub.subject_name,
    sub.max_marks,
    m.marks_obtained,
    ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS subject_percentage
FROM marks m
INNER JOIN student s ON m.student_id = s.student_id
INNER JOIN subject sub ON m.subject_id = sub.subject_id
WHERE s.student_id = 1
ORDER BY sub.subject_id;

-- Query 3.2: Aggregate Result Summary for Student ID = 1
-- Demonstrates: SUM, COUNT, calculated overall percentage
SELECT 
    s.student_id,
    s.name,
    COUNT(m.marks_id) AS subjects_evaluated,
    SUM(m.marks_obtained) AS total_marks_obtained,
    SUM(sub.max_marks) AS total_max_marks,
    ROUND((SUM(m.marks_obtained) / NULLIF(SUM(sub.max_marks), 0)) * 100.0, 2) AS overall_percentage
FROM student s
LEFT JOIN marks m ON s.student_id = m.student_id
LEFT JOIN subject sub ON m.subject_id = sub.subject_id
WHERE s.student_id = 1
GROUP BY s.student_id, s.name;


-- ============================================================================
-- SECTION 4: SUBJECT-WISE PERFORMANCE ANALYTICS (REPORT 2)
-- ============================================================================

-- Query 4.1: Overall Subject Performance Summary
-- Demonstrates: Aggregate functions (COUNT, AVG, MAX, MIN), GROUP BY, and percentage
SELECT 
    sub.subject_id,
    sub.subject_name,
    sub.max_marks,
    COUNT(m.marks_id) AS total_students_evaluated,
    ROUND(AVG(m.marks_obtained), 2) AS average_marks,
    MAX(m.marks_obtained) AS highest_marks,
    MIN(m.marks_obtained) AS lowest_marks,
    ROUND((AVG(m.marks_obtained) / sub.max_marks) * 100.0, 2) AS average_percentage
FROM subject sub
LEFT JOIN marks m ON sub.subject_id = m.subject_id
GROUP BY sub.subject_id, sub.subject_name, sub.max_marks
ORDER BY sub.subject_id;

-- Query 4.2: Top scoring students in Database Management Systems (subject_id = 1)
SELECT 
    s.roll_no,
    s.name,
    s.class_name,
    s.division,
    m.marks_obtained,
    sub.max_marks,
    ROUND((m.marks_obtained / sub.max_marks) * 100.0, 2) AS percentage
FROM marks m
INNER JOIN student s ON m.student_id = s.student_id
INNER JOIN subject sub ON m.subject_id = sub.subject_id
WHERE sub.subject_id = 1
ORDER BY m.marks_obtained DESC
LIMIT 3;


-- ============================================================================
-- SECTION 5: CLASS & DIVISION SUMMARY (REPORT 3)
-- ============================================================================

-- Query 5.1: Performance aggregated by Class and Division
-- Note: Subqueries or DISTINCT counts are used to avoid double-counting students in joins.
SELECT 
    s.class_name,
    s.division,
    COUNT(DISTINCT s.student_id) AS total_students,
    COUNT(m.marks_id) AS total_marks_records,
    COALESCE(ROUND(AVG((m.marks_obtained / sub.max_marks) * 100.0), 2), 0.00) AS class_average_percentage
FROM student s
LEFT JOIN marks m ON s.student_id = m.student_id
LEFT JOIN subject sub ON m.subject_id = sub.subject_id
GROUP BY s.class_name, s.division
ORDER BY s.class_name, s.division;


-- ============================================================================
-- SECTION 6: OUTER JOINS (IDENTIFYING STUDENTS WITHOUT MARKS)
-- ============================================================================

-- Query 6.1: Identify all students who have no marks recorded yet
-- Demonstrates: LEFT OUTER JOIN and IS NULL condition
SELECT 
    s.student_id,
    s.name,
    s.roll_no,
    s.class_name,
    s.division
FROM student s
LEFT JOIN marks m ON s.student_id = m.student_id
WHERE m.marks_id IS NULL
ORDER BY s.class_name, s.division, s.roll_no;


-- ============================================================================
-- SECTION 7: LIVE DASHBOARD METRICS QUERY
-- ============================================================================

-- Query 7.1: Single-query live overview for Dashboard KPI cards
SELECT 
    (SELECT COUNT(*) FROM student) AS total_students,
    (SELECT COUNT(*) FROM subject) AS total_subjects,
    (SELECT COUNT(*) FROM marks) AS total_marks_records,
    (SELECT COUNT(DISTINCT student_id) FROM marks) AS students_with_marks,
    (SELECT COUNT(*) FROM student s WHERE NOT EXISTS (SELECT 1 FROM marks m WHERE m.student_id = s.student_id)) AS students_without_marks,
    (SELECT COALESCE(ROUND(AVG((m.marks_obtained / sub.max_marks) * 100.0), 2), 0.00) 
     FROM marks m 
     JOIN subject sub ON m.subject_id = sub.subject_id) AS overall_average_percentage;


-- ============================================================================
-- SECTION 8: DATABASE INTEGRITY AND CONSTRAINT VALIDATION TESTS
-- (Uncomment individual queries in pgAdmin Query Tool to test expected error behavior)
-- ============================================================================

-- Test 8.1: Test UNIQUE constraint on Student (class_name, division, roll_no)
-- Expected Result: ERROR: duplicate key value violates unique constraint "uq_student_roll"
-- INSERT INTO student (name, roll_no, class_name, division) VALUES ('Duplicate Student', '101', 'TE-COMP', 'A');

-- Test 8.2: Test CHECK constraint on Subject max_marks
-- Expected Result: ERROR: new row for relation "subject" violates check constraint "subject_max_marks_check"
-- INSERT INTO subject (subject_name, max_marks) VALUES ('Invalid Subject', 0);

-- Test 8.3: Test Trigger check_marks_within_max()
-- Expected Result: ERROR: Invalid marks: Obtained score (105.00) exceeds maximum marks (100) for subject "Database Management Systems".
-- INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES (1, 1, 105.00);

-- Test 8.4: Test UNIQUE constraint on Marks (student_id, subject_id)
-- Expected Result: ERROR: duplicate key value violates unique constraint "uq_student_subject"
-- INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES (1, 1, 75.00);

-- Test 8.5: Test Foreign Key RESTRICT on Student Deletion
-- Expected Result: ERROR: update or delete on table "student" violates foreign key constraint "fk_marks_student" on table "marks"
-- DELETE FROM student WHERE student_id = 1;

-- Test 8.6: Test Trigger check_subject_max_marks_update()
-- Expected Result: ERROR: Cannot reduce max_marks to 50 because existing marks for subject "Database Management Systems" reach 95.00.
-- UPDATE subject SET max_marks = 50 WHERE subject_id = 1;
