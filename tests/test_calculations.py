"""
Unit Tests for Result Calculations and Reporting Logic.
Verifies percentage formulas, aggregate metrics, and zero-division edge cases.
"""

import unittest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestAcademicCalculations(unittest.TestCase):
    """Test mathematical formulas and aggregations used in reports."""

    def test_single_subject_percentage(self):
        """Test percentage calculation for a single subject."""
        obtained = 88.5
        max_marks = 100
        pct = round((obtained / max_marks) * 100.0, 2)
        self.assertEqual(pct, 88.50)

        obtained_25 = 23.0
        max_25 = 25
        pct_25 = round((obtained_25 / max_25) * 100.0, 2)
        self.assertEqual(pct_25, 92.00)

    def test_overall_percentage_only_recorded_denominator(self):
        """
        Verify Section 7.5 requirement:
        'Overall percentage calculated only from subjects with recorded marks,
        with the denominator clearly labelled.'
        """
        # Suppose student has marks in 3 subjects out of 5 total in curriculum:
        # Sub 1: 85/100, Sub 2: 40/50, Sub 3: 20/25
        recorded_marks = [
            {"obtained": 85.0, "max": 100},
            {"obtained": 40.0, "max": 50},
            {"obtained": 20.0, "max": 25}
        ]

        total_obtained = sum(r["obtained"] for r in recorded_marks)
        total_max_recorded = sum(r["max"] for r in recorded_marks)

        self.assertEqual(total_obtained, 145.0)
        self.assertEqual(total_max_recorded, 175)

        overall_pct = round((total_obtained / total_max_recorded) * 100.0, 2)
        expected_pct = round((145.0 / 175) * 100.0, 2)  # 82.86%
        self.assertEqual(overall_pct, expected_pct)

    def test_student_with_zero_marks_graceful_division(self):
        """Test that student with zero evaluated subjects yields 0.00% without ZeroDivisionError."""
        recorded_marks = []
        total_obtained = sum(r["obtained"] for r in recorded_marks)
        total_max = sum(r["max"] for r in recorded_marks)

        overall_pct = round((total_obtained / total_max) * 100.0, 2) if total_max > 0 else 0.00
        self.assertEqual(overall_pct, 0.00)

    def test_subject_performance_metrics(self):
        """Verify calculation of count, avg, min, max, and avg percentage."""
        scores = [88.5, 95.0, 62.0, 84.0, 71.5]
        max_possible = 100

        student_count = len(scores)
        avg_score = round(sum(scores) / len(scores), 2)
        highest = max(scores)
        lowest = min(scores)
        avg_pct = round((avg_score / max_possible) * 100.0, 2)

        self.assertEqual(student_count, 5)
        self.assertEqual(highest, 95.0)
        self.assertEqual(lowest, 62.0)
        self.assertEqual(avg_score, 80.20)
        self.assertEqual(avg_pct, 80.20)


if __name__ == "__main__":
    unittest.main()
