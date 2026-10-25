"""
Results & Performance View Module.
Provides detailed Student Marksheets (Section 7.5) and
Subject-wise Performance Analytics (Section 7.6) with live SQL calculations.
"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict, Any
from services.report_service import get_student_result, get_subject_performance
from services.marks_service import get_student_dropdown_options, get_subject_dropdown_options
from database import DatabaseConnectionError, DatabaseError


class ResultsView(ttk.Frame):
    """
    Unified performance view containing:
      Tab 1: Student-wise Marksheet & Overall Results
      Tab 2: Subject-wise Performance & Score Distribution
    """

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, style="Content.TFrame")
        self.student_options: List[Dict[str, Any]] = []
        self.subject_options: List[Dict[str, Any]] = []

        self._build_ui()

    def refresh(self):
        """Reload options and results when view is activated."""
        self.reload_options()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self, style="Content.TFrame")
        header.pack(fill=tk.X, padx=25, pady=(20, 10))

        title_lbl = ttk.Label(
            header,
            text="Academic Results & Performance Analytics",
            font=("Segoe UI", 18, "bold"),
            foreground="#0F172A",
            background="#F8FAFC"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            header,
            text="Individual marksheets and subject score analytics calculated using PostgreSQL SQL joins and aggregates",
            font=("Segoe UI", 10),
            foreground="#64748B",
            background="#F8FAFC"
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Notebook for two modes
        notebook_frame = ttk.Frame(self, style="Content.TFrame")
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Student Marksheet
        self.student_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(self.student_tab, text="  👨‍🎓 Student Marksheet  ")
        self._build_student_tab()

        # Tab 2: Subject Performance
        self.subject_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(self.subject_tab, text="  📈 Subject Performance  ")
        self._build_subject_tab()

    # =========================================================================
    # TAB 1: STUDENT MARKSHEET
    # =========================================================================
    def _build_student_tab(self):
        top_bar = ttk.Frame(self.student_tab, style="Content.TFrame")
        top_bar.pack(fill=tk.X, pady=(15, 10))

        ttk.Label(top_bar, text="Select Student:", font=("Segoe UI", 10, "bold"), background="#F8FAFC").pack(side=tk.LEFT, padx=(0, 8))
        self.student_select_var = tk.StringVar()
        self.student_combo = ttk.Combobox(top_bar, textvariable=self.student_select_var, state="readonly", width=42)
        self.student_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.student_combo.bind("<<ComboboxSelected>>", lambda e: self.load_student_result())

        load_btn = ttk.Button(top_bar, text="Generate Marksheet", command=self.load_student_result, style="Accent.TButton")
        load_btn.pack(side=tk.LEFT, padx=(0, 8))

        export_btn = ttk.Button(top_bar, text="Export CSV", command=self.export_student_marksheet_csv)
        export_btn.pack(side=tk.LEFT)

        # Student Details Card
        self.student_card_frame = tk.Frame(self.student_tab, bg="#FFFFFF", bd=1, relief="solid")
        self.student_card_frame.pack(fill=tk.X, pady=(0, 12))

        self.student_card_inner = tk.Frame(self.student_card_frame, bg="#FFFFFF", padx=16, pady=12)
        self.student_card_inner.pack(fill=tk.X)

        self.student_info_lbl = tk.Label(
            self.student_card_inner,
            text="Please select a student from the dropdown above to view the marksheet.",
            font=("Segoe UI", 10),
            fg="#475569",
            bg="#FFFFFF",
            justify=tk.LEFT
        )
        self.student_info_lbl.pack(side=tk.LEFT)

        self.student_badge_pill = tk.Label(
            self.student_card_inner,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#2563EB"
        )
        self.student_badge_pill.pack(side=tk.RIGHT)

        # Subject Marks Table
        table_container = ttk.Frame(self.student_tab)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        cols = ("sub_id", "subject_name", "max_marks", "obtained", "percentage")
        self.student_tree = ttk.Treeview(table_container, columns=cols, show="headings", height=8, selectmode="browse")

        self.student_tree.heading("sub_id", text="Subject ID")
        self.student_tree.heading("subject_name", text="Subject Title")
        self.student_tree.heading("max_marks", text="Maximum Marks")
        self.student_tree.heading("obtained", text="Marks Obtained")
        self.student_tree.heading("percentage", text="Subject Percentage")

        self.student_tree.column("sub_id", width=90, anchor=tk.CENTER)
        self.student_tree.column("subject_name", width=320, anchor=tk.W)
        self.student_tree.column("max_marks", width=130, anchor=tk.E)
        self.student_tree.column("obtained", width=140, anchor=tk.E)
        self.student_tree.column("percentage", width=140, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=tree_scroll.set)

        self.student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Colored tags for student marksheet
        self.student_tree.tag_configure("tag_distinction", background="#F0FDF4", foreground="#166534")  # >= 85%
        self.student_tree.tag_configure("tag_first_class", background="#EFF6FF", foreground="#1E40AF")   # 70 - 84.99%
        self.student_tree.tag_configure("tag_second_class", background="#FFFBEB", foreground="#92400E")  # < 70%

        # Result Summary KPI Footer with Visual Progress Bar
        self.summary_footer = tk.Frame(self.student_tab, bg="#F8FAFC", bd=1, relief="solid")
        self.summary_footer.pack(fill=tk.X, pady=(0, 10))

        sum_left = tk.Frame(self.summary_footer, bg="#F8FAFC")
        sum_left.pack(side=tk.LEFT, fill=tk.Y, padx=16, pady=10)

        self.summary_lbl = tk.Label(
            sum_left,
            text="Summary: Select a student to compute overall evaluation percentage.",
            font=("Segoe UI", 10, "bold"),
            fg="#1E293B",
            bg="#F8FAFC"
        )
        self.summary_lbl.pack(anchor=tk.W)

        # Right side: Visual Progress Bar & Score Pill
        sum_right = tk.Frame(self.summary_footer, bg="#F8FAFC")
        sum_right.pack(side=tk.RIGHT, padx=16, pady=10)

        self.overall_pct_badge = tk.Label(
            sum_right,
            text="--%",
            font=("Segoe UI", 11, "bold"),
            bg="#E2E8F0",
            fg="#0F172A",
            padx=8,
            pady=2
        )
        self.overall_pct_badge.pack(side=tk.RIGHT, padx=(10, 0))

        self.overall_progressbar = ttk.Progressbar(
            sum_right,
            orient=tk.HORIZONTAL,
            length=180,
            mode='determinate',
            style="Blue.Horizontal.TProgressbar"
        )
        self.overall_progressbar.pack(side=tk.RIGHT)

    def load_student_result(self):
        """Fetch and display student marksheet from PostgreSQL."""
        idx = self.student_combo.current()
        if idx < 0:
            return

        student_id = self.student_options[idx]["student_id"]
        try:
            res = get_student_result(student_id)
            stu = res.get("student")
            subject_marks = res.get("subject_marks", [])
            summary = res.get("summary", {})

            # Update info card
            if stu:
                info_text = f"STUDENT: {stu['name']} (Roll: {stu['roll_no']})"
                self.student_info_lbl.config(
                    text=info_text,
                    fg="#0F172A",
                    font=("Segoe UI", 11, "bold")
                )
                self.student_badge_pill.config(
                    text=f" CLASS: {stu['class_name']}  |  DIV: {stu['division']}  |  ID: #{stu['student_id']} ",
                    bg="#EFF6FF",
                    fg="#2563EB",
                    font=("Segoe UI", 9, "bold")
                )

            # Populate table
            for row in self.student_tree.get_children():
                self.student_tree.delete(row)

            if subject_marks:
                for r in subject_marks:
                    pct_val = float(r['percentage'])
                    pct = f"{pct_val:.2f}%"

                    if pct_val >= 85.0:
                        tag = "tag_distinction"
                    elif pct_val >= 70.0:
                        tag = "tag_first_class"
                    else:
                        tag = "tag_second_class"

                    self.student_tree.insert("", tk.END, values=(
                        r["subject_id"],
                        r["subject_name"],
                        r["max_marks"],
                        f"{float(r['marks_obtained']):.2f}",
                        pct
                    ), tags=(tag,))

                # Update summary
                total_obt = summary.get("total_obtained", 0.0)
                total_max = summary.get("total_max", 0)
                overall_pct = float(summary.get("overall_percentage", 0.0))
                sub_count = summary.get("subjects_count", 0)

                summary_str = (
                    f"Evaluated Subjects: {sub_count}   |   "
                    f"Total Score: {total_obt:.2f} / {total_max} Marks   |   "
                    f"Overall Performance: {overall_pct:.2f}%"
                )
                self.summary_lbl.config(text=summary_str, fg="#15803D")

                # Update Progress Bar and Score Badge
                self.overall_progressbar['value'] = min(max(overall_pct, 0), 100)
                if overall_pct >= 85.0:
                    self.overall_progressbar.config(style="Green.Horizontal.TProgressbar")
                    self.overall_pct_badge.config(
                        text=f" {overall_pct:.1f}%  DISTINCTION ",
                        bg="#DCFCE7",
                        fg="#15803D"
                    )
                elif overall_pct >= 70.0:
                    self.overall_progressbar.config(style="Blue.Horizontal.TProgressbar")
                    self.overall_pct_badge.config(
                        text=f" {overall_pct:.1f}%  FIRST CLASS ",
                        bg="#DBEAFE",
                        fg="#1E40AF"
                    )
                else:
                    self.overall_progressbar.config(style="Amber.Horizontal.TProgressbar")
                    self.overall_pct_badge.config(
                        text=f" {overall_pct:.1f}%  PASS / SECOND ",
                        bg="#FEF3C7",
                        fg="#B45309"
                    )
            else:
                self.student_tree.insert("", tk.END, values=("-", "No marks records found for this student.", "-", "-", "-"))
                self.summary_lbl.config(
                    text="Zero marks records found. (No evaluated subjects recorded).",
                    fg="#9A3412"
                )
                self.overall_progressbar['value'] = 0
                self.overall_pct_badge.config(text=" NO MARKS ", bg="#FEE2E2", fg="#B91C1C")

        except DatabaseError as de:
            messagebox.showerror("Query Error", f"Failed to retrieve student result: {de}")

    def export_student_marksheet_csv(self):
        """Export current student marksheet to a CSV file."""
        if not self.student_tree.get_children():
            messagebox.showinfo("Export Notice", "No marksheet data currently displayed to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Student Marksheet As CSV"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Student Information", self.student_info_lbl.cget("text")])
                writer.writerow([])
                writer.writerow(["Subject ID", "Subject Title", "Maximum Marks", "Marks Obtained", "Percentage"])
                for row_id in self.student_tree.get_children():
                    vals = self.student_tree.item(row_id)["values"]
                    writer.writerow(vals)
                writer.writerow([])
                writer.writerow(["Summary", self.summary_lbl.cget("text")])
            messagebox.showinfo("Export Successful", f"Marksheet successfully exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write CSV file: {e}")

    # =========================================================================
    # TAB 2: SUBJECT PERFORMANCE
    # =========================================================================
    def _build_subject_tab(self):
        top_bar = ttk.Frame(self.subject_tab, style="Content.TFrame")
        top_bar.pack(fill=tk.X, pady=(15, 10))

        ttk.Label(top_bar, text="Select Subject:", font=("Segoe UI", 10, "bold"), background="#F8FAFC").pack(side=tk.LEFT, padx=(0, 8))
        self.subject_select_var = tk.StringVar()
        self.subject_combo = ttk.Combobox(top_bar, textvariable=self.subject_select_var, state="readonly", width=42)
        self.subject_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.subject_combo.bind("<<ComboboxSelected>>", lambda e: self.load_subject_performance())

        load_btn = ttk.Button(top_bar, text="Analyze Performance", command=self.load_subject_performance, style="Accent.TButton")
        load_btn.pack(side=tk.LEFT, padx=(0, 8))

        export_btn = ttk.Button(top_bar, text="Export CSV", command=self.export_subject_performance_csv)
        export_btn.pack(side=tk.LEFT)

        # Subject KPI Summary Tiles
        self.sub_metrics_frame = ttk.Frame(self.subject_tab, style="Content.TFrame")
        self.sub_metrics_frame.pack(fill=tk.X, pady=(0, 12))

        self.sub_metric_labels = {}
        sub_cards = [
            ("count", "Students Evaluated", "0"),
            ("avg", "Average Marks", "0.00"),
            ("high", "Highest Marks", "0.00"),
            ("low", "Lowest Marks", "0.00"),
            ("pct", "Average Percentage", "0.00%")
        ]
        for i, (key, title, def_val) in enumerate(sub_cards):
            card_bd = tk.Frame(self.sub_metrics_frame, bg="#CBD5E1", bd=1)
            card_bd.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            card = tk.Frame(card_bd, bg="#FFFFFF", padx=10, pady=8)
            card.pack(fill=tk.BOTH, expand=True)

            t_lbl = tk.Label(card, text=title.upper(), font=("Segoe UI", 7, "bold"), fg="#64748B", bg="#FFFFFF")
            t_lbl.pack(anchor=tk.W)

            v_lbl = tk.Label(card, text=def_val, font=("Segoe UI", 14, "bold"), fg="#0F172A", bg="#FFFFFF")
            v_lbl.pack(anchor=tk.W, pady=(2, 0))

            self.sub_metric_labels[key] = v_lbl

        # Student Scores Table
        table_container = ttk.Frame(self.subject_tab)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        cols = ("roll", "name", "class_div", "obtained", "percentage")
        self.subject_tree = ttk.Treeview(table_container, columns=cols, show="headings", height=8, selectmode="browse")

        self.subject_tree.heading("roll", text="Roll No")
        self.subject_tree.heading("name", text="Student Name")
        self.subject_tree.heading("class_div", text="Class & Division")
        self.subject_tree.heading("obtained", text="Marks Obtained")
        self.subject_tree.heading("percentage", text="Percentage")

        self.subject_tree.column("roll", width=90, anchor=tk.CENTER)
        self.subject_tree.column("name", width=240, anchor=tk.W)
        self.subject_tree.column("class_div", width=130, anchor=tk.CENTER)
        self.subject_tree.column("obtained", width=130, anchor=tk.E)
        self.subject_tree.column("percentage", width=130, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.subject_tree.yview)
        self.subject_tree.configure(yscrollcommand=tree_scroll.set)

        self.subject_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Percentage color tags
        self.subject_tree.tag_configure("tag_distinction", background="#F0FDF4", foreground="#166534")  # >= 85%
        self.subject_tree.tag_configure("tag_first_class", background="#EFF6FF", foreground="#1E40AF")   # 70 - 84.99%
        self.subject_tree.tag_configure("tag_second_class", background="#FFFBEB", foreground="#92400E")  # < 70%

    def load_subject_performance(self):
        """Fetch and display subject performance distribution from PostgreSQL."""
        idx = self.subject_combo.current()
        if idx < 0:
            return

        subject_id = self.subject_options[idx]["subject_id"]
        try:
            data = get_subject_performance(subject_id)
            scores = data.get("student_scores", [])
            m = data.get("metrics", {})

            # Update KPI cards
            self.sub_metric_labels["count"].config(text=str(m.get("student_count", 0)))
            self.sub_metric_labels["avg"].config(text=f"{float(m.get('average_marks', 0.0)):.2f}")
            self.sub_metric_labels["high"].config(text=f"{float(m.get('highest_marks', 0.0)):.2f}")
            self.sub_metric_labels["low"].config(text=f"{float(m.get('lowest_marks', 0.0)):.2f}")
            self.sub_metric_labels["pct"].config(text=f"{float(m.get('average_percentage', 0.0)):.2f}%")

            # Update table
            for row in self.subject_tree.get_children():
                self.subject_tree.delete(row)

            if scores:
                for s in scores:
                    class_div = f"{s.get('class_name', '')} - {s.get('division', '')}"
                    pct_val = float(s['percentage'])
                    pct = f"{pct_val:.2f}%"

                    if pct_val >= 85.0:
                        tag = "tag_distinction"
                    elif pct_val >= 70.0:
                        tag = "tag_first_class"
                    else:
                        tag = "tag_second_class"

                    self.subject_tree.insert("", tk.END, values=(
                        s["roll_no"],
                        s["student_name"],
                        class_div,
                        f"{float(s['marks_obtained']):.2f}",
                        pct
                    ), tags=(tag,))
            else:
                self.subject_tree.insert("", tk.END, values=("-", "No student marks recorded for this subject.", "-", "-", "-"))

        except DatabaseError as de:
            messagebox.showerror("Query Error", f"Failed to retrieve subject analytics: {de}")

    def export_subject_performance_csv(self):
        """Export subject performance table to CSV."""
        if not self.subject_tree.get_children():
            messagebox.showinfo("Export Notice", "No subject data currently displayed to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Subject Performance As CSV"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Subject", self.subject_select_var.get()])
                writer.writerow(["Roll No", "Student Name", "Class & Division", "Marks Obtained", "Percentage"])
                for row_id in self.subject_tree.get_children():
                    vals = self.subject_tree.item(row_id)["values"]
                    writer.writerow(vals)
            messagebox.showinfo("Export Successful", f"Subject performance exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write CSV file: {e}")

    def reload_options(self):
        """Reload student and subject combobox options."""
        try:
            self.student_options = get_student_dropdown_options()
            self.student_combo["values"] = [s["display"] for s in self.student_options]
            if self.student_options and not self.student_select_var.get():
                self.student_combo.current(0)
                self.load_student_result()

            self.subject_options = get_subject_dropdown_options()
            self.subject_combo["values"] = [sub["display"] for sub in self.subject_options]
            if self.subject_options and not self.subject_select_var.get():
                self.subject_combo.current(0)
                self.load_subject_performance()
        except Exception:
            pass
