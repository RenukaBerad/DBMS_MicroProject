"""
Unit Tests for Business Logic, Input Validation, and Edge Cases.
These tests run offline and verify data integrity rules without needing a live database.
"""

import unittest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.student_service import validate_student_input
from services.subject_service import validate_subject_input
from config import DatabaseConfig


class TestInputValidation(unittest.TestCase):
    """Test validation functions enforcing relational and business constraints."""

    # -------------------------------------------------------------------------
    # 1. STUDENT VALIDATION TESTS
    # -------------------------------------------------------------------------
    def test_valid_student_input(self):
        """Verify normal student data passes validation."""
        is_valid, msg = validate_student_input("Aarav Sharma", "101", "TE-COMP", "A")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_student_empty_name(self):
        """Reject blank student name."""
        is_valid, msg = validate_student_input("", "101", "TE-COMP", "A")
        self.assertFalse(is_valid)
        self.assertIn("Name cannot be empty", msg)

    def test_student_empty_roll_no(self):
        """Reject blank roll number."""
        is_valid, msg = validate_student_input("Aarav Sharma", "   ", "TE-COMP", "A")
        self.assertFalse(is_valid)
        self.assertIn("Roll Number cannot be empty", msg)

    def test_student_empty_class(self):
        """Reject blank class name."""
        is_valid, msg = validate_student_input("Aarav Sharma", "101", "", "A")
        self.assertFalse(is_valid)
        self.assertIn("Class cannot be empty", msg)

    def test_student_empty_division(self):
        """Reject blank division."""
        is_valid, msg = validate_student_input("Aarav Sharma", "101", "TE-COMP", "")
        self.assertFalse(is_valid)
        self.assertIn("Division cannot be empty", msg)

    def test_student_name_excessive_length(self):
        """Reject student name exceeding VARCHAR(100)."""
        long_name = "A" * 105
        is_valid, msg = validate_student_input(long_name, "101", "TE-COMP", "A")
        self.assertFalse(is_valid)
        self.assertIn("cannot exceed 100 characters", msg)

    # -------------------------------------------------------------------------
    # 2. SUBJECT VALIDATION TESTS
    # -------------------------------------------------------------------------
    def test_valid_subject_input(self):
        """Verify valid subject name and max marks."""
        is_valid, msg, max_m = validate_subject_input("Database Management Systems", 100)
        self.assertTrue(is_valid)
        self.assertEqual(max_m, 100)

    def test_subject_empty_name(self):
        """Reject blank subject title."""
        is_valid, msg, max_m = validate_subject_input("", 100)
        self.assertFalse(is_valid)
        self.assertIn("Subject Name cannot be empty", msg)

    def test_subject_zero_max_marks(self):
        """Reject max_marks = 0 (violates CHECK max_marks > 0)."""
        is_valid, msg, max_m = validate_subject_input("Operating Systems", 0)
        self.assertFalse(is_valid)
        self.assertIn("strictly greater than 0", msg)

    def test_subject_negative_max_marks(self):
        """Reject negative max_marks."""
        is_valid, msg, max_m = validate_subject_input("Operating Systems", -50)
        self.assertFalse(is_valid)
        self.assertIn("strictly greater than 0", msg)

    def test_subject_non_integer_max_marks(self):
        """Reject alphanumeric max_marks string."""
        is_valid, msg, max_m = validate_subject_input("Theory of Computation", "one_hundred")
        self.assertFalse(is_valid)
        self.assertIn("must be an integer", msg)

    # -------------------------------------------------------------------------
    # 3. CONFIGURATION TESTS
    # -------------------------------------------------------------------------
    def test_config_placeholder_detection(self):
        """Verify config detects placeholder password."""
        cfg = DatabaseConfig(password="replace_with_your_local_password")
        self.assertTrue(cfg.is_placeholder_password())

        cfg_valid = DatabaseConfig(password="secret_pass_123")
        self.assertFalse(cfg_valid.is_placeholder_password())

    def test_config_display_target(self):
        """Verify password is not exposed in display target."""
        cfg = DatabaseConfig(
            host="localhost",
            port=5432,
            database="internal_marks_db",
            user="postgres",
            password="super_secret_password"
        )
        display = cfg.display_target
        self.assertNotIn("super_secret_password", display)
        self.assertEqual(display, "postgres@localhost:5432/internal_marks_db")


if __name__ == "__main__":
    unittest.main()
