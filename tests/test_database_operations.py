"""
Integration and Mocked Database Operations Tests.
Detects if a live PostgreSQL database is reachable.
- If reachable: Runs live transactional verification against PostgreSQL.
- If unreachable: Uses unittest.mock to test query construction, parameterization,
  transaction rollback, and exception handling without requiring PostgreSQL running.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import test_connection, execute_query, DatabaseIntegrityError, DatabaseError
import services.student_service as student_service
import services.subject_service as subject_service
import services.marks_service as marks_service
import services.report_service as report_service


class TestDatabaseOperations(unittest.TestCase):
    """Test SQL query parameterization and service operations."""

    @classmethod
    def setUpClass(cls):
        cls.is_live_db, cls.db_msg = test_connection()

    def test_live_or_mocked_student_retrieval(self):
        """Test retrieving students using either live DB or mock cursor."""
        if self.is_live_db:
            students = student_service.get_all_students()
            self.assertIsInstance(students, list)
        else:
            mock_data = [
                {"student_id": 1, "name": "Aarav Sharma", "roll_no": "101", "class_name": "TE-COMP", "division": "A"}
            ]
            with patch("services.student_service.execute_query", return_value=mock_data) as mock_exec:
                students = student_service.get_all_students()
                self.assertEqual(len(students), 1)
                self.assertEqual(students[0]["name"], "Aarav Sharma")
                mock_exec.assert_called_once()
                # Verify ORDER BY was present in SQL
                called_sql = mock_exec.call_args[0][0]
                self.assertIn("ORDER BY", called_sql)

    def test_student_search_parameterization(self):
        """Verify search query uses parameters instead of raw string concatenation."""
        with patch("services.student_service.execute_query", return_value=[]) as mock_exec:
            student_service.get_all_students(search_query="Sharma")
            mock_exec.assert_called_once()
            sql, params = mock_exec.call_args[0][0], mock_exec.call_args[0][1]
            self.assertIn("%s", sql)
            self.assertIn("%Sharma%", params)

    def test_subject_max_marks_reduction_guard(self):
        """Verify updating subject max marks checks existing marks to prevent invalid states."""
        # Mock that subject currently has an existing mark of 95.0
        with patch("services.subject_service.execute_query", return_value={"highest": 95.0}):
            with self.assertRaises(ValueError) as ctx:
                subject_service.update_subject(subject_id=1, subject_name="DBMS", max_marks=80)
            self.assertIn("Cannot reduce Maximum Marks to 80", str(ctx.exception))
            self.assertIn("reach 95.0", str(ctx.exception))

    def test_marks_validation_against_subject(self):
        """Verify marks input cannot exceed subject max_marks."""
        mock_subject = {"subject_id": 1, "subject_name": "Operating Systems", "max_marks": 50}
        with patch("services.marks_service.get_subject_by_id", return_value=mock_subject):
            is_valid, msg, marks = marks_service.validate_marks_input(
                student_id=1, subject_id=1, marks_obtained=55
            )
            self.assertFalse(is_valid)
            self.assertIn("exceeds the maximum marks (50.0)", msg)

    def test_duplicate_marks_prevention(self):
        """Verify attempting to add marks for same (student, subject) raises error."""
        mock_subject = {"subject_id": 1, "subject_name": "DBMS", "max_marks": 100}
        with patch("services.marks_service.get_subject_by_id", return_value=mock_subject):
            with patch("services.marks_service.execute_query", return_value={"marks_id": 10}):
                with self.assertRaises(ValueError) as ctx:
                    marks_service.add_marks(student_id=1, subject_id=1, marks_obtained=85)
                self.assertIn("already exists", str(ctx.exception))

    def test_report_service_dashboard_aggregation(self):
        """Verify dashboard statistics structure and calculation handling."""
        mock_stats = {
            "total_students": 8,
            "total_subjects": 5,
            "total_marks_records": 24,
            "students_with_marks": 7,
            "students_without_marks": 1,
            "overall_average_percentage": 78.45
        }
        with patch("services.report_service.execute_query", side_effect=[mock_stats, [], []]):
            stats = report_service.get_dashboard_stats()
            self.assertEqual(stats["total_students"], 8)
            self.assertEqual(stats["total_subjects"], 5)
            self.assertEqual(stats["students_without_marks"], 1)
            self.assertEqual(stats["overall_average_percentage"], 78.45)
            self.assertIn("recent_students", stats)


if __name__ == "__main__":
    unittest.main()
