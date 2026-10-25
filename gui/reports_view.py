"""
Reports View Module.
Executes and displays real SQL analytical reports:
  Report 1: Student-wise Marks Ledger (SELECT, JOIN, WHERE, ORDER BY)
  Report 2: Subject-wise Performance Summary (JOIN, COUNT, AVG, MAX, MIN, GROUP BY)
  Report 3: Class & Division Aggregate Summary (JOIN, GROUP BY, COUNT DISTINCT, AVG)
  Report 4: Students With Zero Recorded Marks (LEFT JOIN, IS NULL)
Includes CSV export and viva-friendly SQL Query Viewer.
"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict, Any
from services.report_service import (
    get_report_student_wise_marks,
    get_report_subject_performance,
    get_report_class_division_summary,
    get_report_students_without_marks
)
from services.student_service import get_distinct_classes_and_divisions
from services.marks_service import get_subject_dropdown_options
from database import DatabaseConnectionError, DatabaseError


class ReportsView(ttk.Frame):
    """
    Dedicated Reports section with SQL query execution,
    clean tabular output, filtering, and CSV export.
    """

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, style="Content.TFrame")
        self.active_report_index = 0
        self.subject_options: List[Dict[str, Any]] = []

        self._build_ui()

    def refresh(self):
        """Fetch latest filters and rerun the active report."""
        self.reload_filters()
        self.run_active_report()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self, style="Content.TFrame")
        header.pack(fill=tk.X, padx=25, pady=(20, 10))

        title_box = ttk.Frame(header, style="Content.TFrame")
        title_box.pack(side=tk.LEFT)

        title_lbl = ttk.Label(
            title_box,
            text="SQL Analytics & Reports",
            font=("Segoe UI", 18, "bold"),
            foreground="#0F172A",
            background="#F8FAFC"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            title_box,
            text="Real-time reports generated from PostgreSQL queries using JOINs, aggregates, and groupings",
            font=("Segoe UI", 10),
            foreground="#64748B",
            background="#F8FAFC"
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Action Buttons on Header
        btn_box = ttk.Frame(header, style="Content.TFrame")
        btn_box.pack(side=tk.RIGHT, pady=5)

        export_btn = ttk.Button(btn_box, text="📥 Export CSV", command=self.export_csv, style="Accent.TButton")
        export_btn.pack(side=tk.LEFT, padx=(0, 6))

        refresh_btn = ttk.Button(btn_box, text="⟳ Refresh Report", command=self.run_active_report)
        refresh_btn.pack(side=tk.LEFT)

        # Report Selector Bar
        selector_frame = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid")
        selector_frame.pack(fill=tk.X, padx=25, pady=(5, 10))

        selector_inner = tk.Frame(selector_frame, bg="#FFFFFF", padx=10, pady=8)
        selector_inner.pack(fill=tk.X)

        tk.Label(selector_inner, text="Select Report:", font=("Segoe UI", 10, "bold"), fg="#1E293B", bg="#FFFFFF").pack(side=tk.LEFT, padx=(5, 10))

        self.report_titles = [
            "Report 1: Student-wise Marks Report (SELECT, JOIN, WHERE, ORDER BY)",
            "Report 2: Subject-wise Performance (COUNT, AVG, MAX, MIN, GROUP BY)",
            "Report 3: Class & Division Summary (JOIN, GROUP BY, DISTINCT COUNT)",
            "Report 4: Students With No Marks Recorded (LEFT JOIN, IS NULL)"
        ]

        self.report_selector_var = tk.StringVar(value=self.report_titles[0])
        self.report_combo = ttk.Combobox(
            selector_inner,
            textvariable=self.report_selector_var,
            values=self.report_titles,
            state="readonly",
            width=58
        )
        self.report_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.report_combo.bind("<<ComboboxSelected>>", self.on_report_selection_changed)

        # Filter Sub-bar (used for Report 1)
        self.filter_sub_frame = tk.Frame(selector_inner, bg="#FFFFFF")
        self.filter_sub_frame.pack(side=tk.LEFT, fill=tk.X)

        tk.Label(self.filter_sub_frame, text="Class:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#FFFFFF").pack(side=tk.LEFT, padx=(5, 2))
        self.class_var = tk.StringVar(value="ALL")
        self.class_combo = ttk.Combobox(self.filter_sub_frame, textvariable=self.class_var, state="readonly", width=10)
        self.class_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.class_combo.bind("<<ComboboxSelected>>", lambda e: self.run_active_report())

        tk.Label(self.filter_sub_frame, text="Div:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 2))
        self.div_var = tk.StringVar(value="ALL")
        self.div_combo = ttk.Combobox(self.filter_sub_frame, textvariable=self.div_var, state="readonly", width=6)
        self.div_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.div_combo.bind("<<ComboboxSelected>>", lambda e: self.run_active_report())

        # Description and SQL query preview box
        self.info_frame = tk.Frame(self, bg="#F1F5F9", padx=12, pady=6)
        self.info_frame.pack(fill=tk.X, padx=25, pady=(0, 8))

        self.info_lbl = tk.Label(
            self.info_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#334155",
            bg="#F1F5F9",
            justify=tk.LEFT
        )
        self.info_lbl.pack(side=tk.LEFT)

        # Table container
        table_container = ttk.Frame(self)
        table_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 15))

        self.tree = ttk.Treeview(table_container, show="headings", selectmode="browse")
        tree_scroll_y = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.tree.xview)

        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Percentage color tags
        self.tree.tag_configure("tag_distinction", background="#F0FDF4", foreground="#166534")  # >= 85%
        self.tree.tag_configure("tag_first_class", background="#EFF6FF", foreground="#1E40AF")   # 70 - 84.99%
        self.tree.tag_configure("tag_second_class", background="#FFFBEB", foreground="#92400E")  # < 70%
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F8FAFC")

    def reload_filters(self):
        """Fetch distinct classes and divisions for report filtering."""
        try:
            classes, divs = get_distinct_classes_and_divisions()
            self.class_combo["values"] = ["ALL"] + classes
            self.div_combo["values"] = ["ALL"] + divs
            self.subject_options = get_subject_dropdown_options()
        except Exception:
            pass

    def on_report_selection_changed(self, event=None):
        """Handle switching report in the combobox."""
        self.active_report_index = self.report_combo.current()
        # Toggle filter visibility for report 1
        if self.active_report_index == 0:
            self.filter_sub_frame.pack(side=tk.LEFT, fill=tk.X)
        else:
            self.filter_sub_frame.pack_forget()

        self.run_active_report()

    def run_active_report(self):
        """Run the active SQL report and populate the treeview."""
        # Clear existing columns and rows
        self.tree.delete(*self.tree.get_children())

        idx = self.active_report_index
        try:
            if idx == 0:
                self._run_report_student_wise()
            elif idx == 1:
                self._run_report_subject_performance()
            elif idx == 2:
                self._run_report_class_division()
            elif idx == 3:
                self._run_report_students_without_marks()
        except DatabaseConnectionError:
            self._set_tree_columns(["Status"], [("Database connection offline. Please check .env credentials.",)])
        except DatabaseError as de:
            self._set_tree_columns(["Error"], [(f"SQL Execution Error: {de}",)])

    def _set_tree_columns(self, col_names: List[str], rows: List[tuple], col_widths: Optional[Dict[str, int]] = None, tags_list: Optional[List[str]] = None):
        """Helper to reconfigure Treeview columns dynamically with row tags."""
        self.tree["columns"] = col_names
        for c in col_names:
            self.tree.heading(c, text=c)
            width = col_widths.get(c, 140) if col_widths else 140
            anchor = tk.E if "Marks" in c or "Percentage" in c or "Count" in c or "Score" in c else (tk.CENTER if "ID" in c or "Div" in c or "Roll" in c else tk.W)
            self.tree.column(c, width=width, anchor=anchor)

        for i, r in enumerate(rows):
            t = (tags_list[i],) if tags_list and i < len(tags_list) and tags_list[i] else ()
            self.tree.insert("", tk.END, values=r, tags=t)

    def _run_report_student_wise(self):
        """Report 1: Student-wise Marks Report."""
        self.info_lbl.config(
            text="Query Concept: 3-Table INNER JOIN (marks + student + subject) with calculated percentage and multi-column ordering."
        )
        c_filter = self.class_var.get()
        d_filter = self.div_var.get()

        data = get_report_student_wise_marks(class_filter=c_filter, division_filter=d_filter)

        cols = ["Student ID", "Roll No", "Student Name", "Class", "Div", "Subject", "Max Marks", "Marks Obtained", "Percentage"]
        widths = {
            "Student ID": 80, "Roll No": 80, "Student Name": 180, "Class": 90, "Div": 60,
            "Subject": 220, "Max Marks": 90, "Marks Obtained": 110, "Percentage": 100
        }

        rows = []
        tags = []
        if data:
            for r in data:
                pct_val = float(r['percentage'])
                if pct_val >= 85.0:
                    tag = "tag_distinction"
                elif pct_val >= 70.0:
                    tag = "tag_first_class"
                else:
                    tag = "tag_second_class"

                rows.append((
                    r["student_id"],
                    r["roll_no"],
                    r["student_name"],
                    r["class_name"],
                    r["division"],
                    r["subject_name"],
                    r["max_marks"],
                    f"{float(r['marks_obtained']):.2f}",
                    f"{pct_val:.2f}%"
                ))
                tags.append(tag)
        else:
            rows.append(("-", "-", "No marks records matching filter criteria", "-", "-", "-", "-", "-", "-"))
            tags.append("")

        self._set_tree_columns(cols, rows, widths, tags_list=tags)

    def _run_report_subject_performance(self):
        """Report 2: Subject-wise Performance."""
        self.info_lbl.config(
            text="Query Concept: LEFT JOIN and Aggregate Functions: COUNT(marks_id), AVG(marks_obtained), MAX, MIN grouped by Subject."
        )
        data = get_report_subject_performance()

        cols = ["Subject ID", "Subject Title", "Max Marks", "Evaluations Count", "Avg Marks", "Highest Marks", "Lowest Marks", "Average Percentage"]
        widths = {
            "Subject ID": 90, "Subject Title": 260, "Max Marks": 100, "Evaluations Count": 120,
            "Avg Marks": 100, "Highest Marks": 105, "Lowest Marks": 105, "Average Percentage": 130
        }

        rows = []
        tags = []
        if data:
            for r in data:
                pct_val = float(r['average_percentage'])
                if pct_val >= 85.0:
                    tag = "tag_distinction"
                elif pct_val >= 70.0:
                    tag = "tag_first_class"
                else:
                    tag = "tag_second_class"

                rows.append((
                    r["subject_id"],
                    r["subject_name"],
                    r["max_marks"],
                    r["total_records"],
                    f"{float(r['average_marks']):.2f}",
                    f"{float(r['highest_marks']):.2f}",
                    f"{float(r['lowest_marks']):.2f}",
                    f"{pct_val:.2f}%"
                ))
                tags.append(tag)
        else:
            rows.append(("-", "No subject records found", "-", "-", "-", "-", "-", "-"))
            tags.append("")

        self._set_tree_columns(cols, rows, widths, tags_list=tags)

    def _run_report_class_division(self):
        """Report 3: Class and Division Summary."""
        self.info_lbl.config(
            text="Query Concept: JOIN with GROUP BY class_name, division. Uses COUNT(DISTINCT student_id) to avoid join cartesian multiplication."
        )
        data = get_report_class_division_summary()

        cols = ["Class", "Division", "Total Registered Students", "Total Marks Records", "Class Average Percentage"]
        widths = {
            "Class": 120, "Division": 90, "Total Registered Students": 180,
            "Total Marks Records": 160, "Class Average Percentage": 180
        }

        rows = []
        tags = []
        if data:
            for r in data:
                pct_val = float(r['average_percentage'])
                if pct_val >= 85.0:
                    tag = "tag_distinction"
                elif pct_val >= 70.0:
                    tag = "tag_first_class"
                else:
                    tag = "tag_second_class"

                rows.append((
                    r["class_name"],
                    r["division"],
                    r["total_students"],
                    r["total_marks_records"],
                    f"{pct_val:.2f}%"
                ))
                tags.append(tag)
        else:
            rows.append(("-", "-", "No records found", "-", "-"))
            tags.append("")

        self._set_tree_columns(cols, rows, widths, tags_list=tags)

    def _run_report_students_without_marks(self):
        """Report 4: Students with No Marks Recorded."""
        self.info_lbl.config(
            text="Query Concept: LEFT OUTER JOIN between student and marks with WHERE marks.marks_id IS NULL to isolate unevaluated students."
        )
        data = get_report_students_without_marks()

        cols = ["Student ID", "Roll No", "Student Name", "Class", "Division", "Evaluation Status"]
        widths = {
            "Student ID": 90, "Roll No": 90, "Student Name": 240, "Class": 110, "Division": 90, "Evaluation Status": 160
        }

        rows = []
        tags = []
        if data:
            for r in data:
                rows.append((
                    r["student_id"],
                    r["roll_no"],
                    r["student_name"],
                    r["class_name"],
                    r["division"],
                    "Pending / No Marks"
                ))
                tags.append("tag_second_class")
        else:
            rows.append(("-", "-", "All students currently have at least one marks record entered.", "-", "-", "-"))
            tags.append("")

        self._set_tree_columns(cols, rows, widths, tags_list=tags)

    def export_csv(self):
        """Export the currently active report table to a CSV file."""
        cols = self.tree["columns"]
        children = self.tree.get_children()
        if not children:
            messagebox.showinfo("Export Notice", "No report data currently available to export.")
            return

        report_name = self.report_selector_var.get().split(":")[0].strip()
        default_filename = f"{report_name.lower().replace(' ', '_')}.csv"

        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Report As CSV"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Report Title", self.report_selector_var.get()])
                writer.writerow(["SQL Note", self.info_lbl.cget("text")])
                writer.writerow([])
                writer.writerow(cols)
                for item_id in children:
                    vals = self.tree.item(item_id)["values"]
                    writer.writerow(vals)
            messagebox.showinfo("Export Complete", f"Report successfully saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to write CSV file: {e}")
