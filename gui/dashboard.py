"""
Dashboard View Module.
Presents live KPI summary metrics, recent assessment entries,
and database status indicators retrieved directly from PostgreSQL.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from services.report_service import get_dashboard_stats
from database import DatabaseConnectionError, DatabaseError


class DashboardView(ttk.Frame):
    """
    Dashboard home view displaying live database statistics
    and recent marks transactions.
    """

    def __init__(self, parent: tk.Widget, navigate_fn: Optional[Callable[[str], None]] = None):
        super().__init__(parent, style="Content.TFrame")
        self.navigate_fn = navigate_fn

        self.kpi_labels = {}
        self._build_ui()
        self.after(50, self.refresh)

    def _build_ui(self):
        # Header banner
        header_frame = ttk.Frame(self, style="Content.TFrame")
        header_frame.pack(fill=tk.X, padx=25, pady=(20, 15))

        title_box = ttk.Frame(header_frame, style="Content.TFrame")
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        title_lbl = ttk.Label(
            title_box,
            text="System Overview & Analytics",
            font=("Segoe UI", 18, "bold"),
            foreground="#0F172A",
            background="#F8FAFC"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            title_box,
            text="Live database statistics retrieved from PostgreSQL",
            font=("Segoe UI", 10),
            foreground="#64748B",
            background="#F8FAFC"
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Action button
        btn_frame = ttk.Frame(header_frame, style="Content.TFrame")
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        refresh_btn = ttk.Button(
            btn_frame,
            text="⟳ Refresh Dashboard",
            command=self.refresh,
            style="Accent.TButton"
        )
        refresh_btn.pack(side=tk.RIGHT, pady=5)

        # Connection Warning Banner (hidden by default)
        self.banner_frame = tk.Frame(self, bg="#FEF2F2", highlightbackground="#F87171", highlightthickness=1)
        self.banner_lbl = tk.Label(
            self.banner_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg="#991B1B",
            bg="#FEF2F2",
            padx=15,
            pady=8
        )
        self.banner_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # KPI Metrics Grid Container
        kpi_container = ttk.Frame(self, style="Content.TFrame")
        kpi_container.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Define 6 metric cards
        cards_data = [
            ("total_students", "Total Students", "0", "#2563EB", "Registered in system"),
            ("total_subjects", "Total Subjects", "0", "#7C3AED", "Active courses"),
            ("total_marks", "Marks Records", "0", "#059669", "Total assessments recorded"),
            ("evaluated_students", "Evaluated Students", "0", "#0284C7", "With at least 1 marks record"),
            ("unevaluated_students", "Pending Students", "0", "#D97706", "Zero marks records recorded"),
            ("overall_avg", "Overall Average", "0.0%", "#DC2626", "Across all evaluated subjects")
        ]

        # 3 columns x 2 rows responsive grid
        for i, (key, title, default_val, accent_color, subtitle) in enumerate(cards_data):
            row = i // 3
            col = i % 3
            card = self._create_kpi_card(kpi_container, title, default_val, accent_color, subtitle)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            kpi_container.columnconfigure(col, weight=1)

        # Bottom Section: Recent Marks Records Table
        recent_section = ttk.Frame(self, style="Content.TFrame")
        recent_section.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))

        sec_header = ttk.Frame(recent_section, style="Content.TFrame")
        sec_header.pack(fill=tk.X, pady=(0, 8))

        sec_title = ttk.Label(
            sec_header,
            text="Recent Activity & Registered Records",
            font=("Segoe UI", 13, "bold"),
            foreground="#0F172A",
            background="#F8FAFC"
        )
        sec_title.pack(side=tk.LEFT)

        sec_hint = ttk.Label(
            sec_header,
            text="Live records committed to PostgreSQL database",
            font=("Segoe UI", 9),
            foreground="#64748B",
            background="#F8FAFC"
        )
        sec_hint.pack(side=tk.LEFT, padx=10)

        # Notebook tabs for Recent Students vs Recent Marks
        self.notebook = ttk.Notebook(recent_section)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Recent Students Tab
        tab_students = ttk.Frame(self.notebook)
        self.notebook.add(tab_students, text="  👥  Recently Registered Students  ")

        std_cols = ("id", "name", "roll", "class_div", "eval_status")
        self.tree_students = ttk.Treeview(tab_students, columns=std_cols, show="headings", height=7, selectmode="browse")
        self.tree_students.heading("id", text="Student ID")
        self.tree_students.heading("name", text="Student Full Name")
        self.tree_students.heading("roll", text="Roll No")
        self.tree_students.heading("class_div", text="Class & Division")
        self.tree_students.heading("eval_status", text="Evaluation Status")

        self.tree_students.column("id", width=80, anchor=tk.CENTER)
        self.tree_students.column("name", width=220, anchor=tk.W)
        self.tree_students.column("roll", width=90, anchor=tk.CENTER)
        self.tree_students.column("class_div", width=130, anchor=tk.CENTER)
        self.tree_students.column("eval_status", width=140, anchor=tk.CENTER)

        std_scroll = ttk.Scrollbar(tab_students, orient=tk.VERTICAL, command=self.tree_students.yview)
        self.tree_students.configure(yscrollcommand=std_scroll.set)
        self.tree_students.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        std_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_students.tag_configure("status_graded", foreground="#166534", background="#F0FDF4")
        self.tree_students.tag_configure("status_pending", foreground="#92400E", background="#FFFBEB")

        # Tab 2: Recent Marks Tab
        tab_marks = ttk.Frame(self.notebook)
        self.notebook.add(tab_marks, text="  📝  Recent Marks Evaluations  ")

        columns = ("id", "roll", "name", "class_div", "subject", "score", "max", "pct")
        self.tree = ttk.Treeview(tab_marks, columns=columns, show="headings", height=7, selectmode="browse")

        self.tree.heading("id", text="Marks ID")
        self.tree.heading("roll", text="Roll No")
        self.tree.heading("name", text="Student Name")
        self.tree.heading("class_div", text="Class & Div")
        self.tree.heading("subject", text="Subject")
        self.tree.heading("score", text="Marks Obtained")
        self.tree.heading("max", text="Max Marks")
        self.tree.heading("pct", text="Percentage")

        self.tree.column("id", width=70, anchor=tk.CENTER)
        self.tree.column("roll", width=80, anchor=tk.CENTER)
        self.tree.column("name", width=180, anchor=tk.W)
        self.tree.column("class_div", width=110, anchor=tk.CENTER)
        self.tree.column("subject", width=220, anchor=tk.W)
        self.tree.column("score", width=110, anchor=tk.E)
        self.tree.column("max", width=90, anchor=tk.E)
        self.tree.column("pct", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tab_marks, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure colored status tags for percentage
        self.tree.tag_configure("tag_distinction", background="#F0FDF4", foreground="#166534")  # >= 85%
        self.tree.tag_configure("tag_first_class", background="#EFF6FF", foreground="#1E40AF")   # 70 - 84.99%
        self.tree.tag_configure("tag_second_class", background="#FFFBEB", foreground="#92400E")  # < 70%

    def _create_kpi_card(self, parent: ttk.Frame, title: str, default_val: str, accent_color: str, subtitle: str) -> tk.Frame:
        """Create an elevated modern enterprise card with top accent bar and status badge."""
        card_border = tk.Frame(parent, bg="#E2E8F0", bd=1)
        card = tk.Frame(card_border, bg="#FFFFFF", padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True)

        # Top color accent bar
        color_bar = tk.Frame(card, bg=accent_color, height=3)
        color_bar.place(x=-16, y=-14, relwidth=1.5, height=3)

        # Header with badge pill
        top_row = tk.Frame(card, bg="#FFFFFF")
        top_row.pack(fill=tk.X)

        title_lbl = tk.Label(
            top_row,
            text=title.upper(),
            font=("Segoe UI", 8, "bold"),
            fg="#64748B",
            bg="#FFFFFF"
        )
        title_lbl.pack(side=tk.LEFT)

        # Badges mapping
        badges = {
            "Total Students": ("STUDENTS", "#EFF6FF", "#2563EB"),
            "Total Subjects": ("COURSES", "#F5F3FF", "#7C3AED"),
            "Marks Records": ("COMMITTED", "#ECFDF5", "#059669"),
            "Evaluated Students": ("GRADED", "#F0F9FF", "#0284C7"),
            "Pending Students": ("PENDING", "#FFFBEB", "#D97706"),
            "Overall Average": ("BENCHMARK", "#FEF2F2", "#DC2626")
        }
        b_text, b_bg, b_fg = badges.get(title, ("ACTIVE", "#F1F5F9", "#475569"))
        badge = tk.Label(
            top_row,
            text=f" {b_text} ",
            font=("Segoe UI", 7, "bold"),
            bg=b_bg,
            fg=b_fg,
            padx=4,
            pady=1
        )
        badge.pack(side=tk.RIGHT)

        val_lbl = tk.Label(
            card,
            text=default_val,
            font=("Segoe UI", 24, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        )
        val_lbl.pack(anchor=tk.W, pady=(6, 2))

        sub_lbl = tk.Label(
            card,
            text=subtitle,
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#FFFFFF"
        )
        sub_lbl.pack(anchor=tk.W)

        # Store reference for live update
        self.kpi_labels[title] = val_lbl
        return card_border

    def refresh(self):
        """Fetch live statistics from PostgreSQL and update cards and table."""
        try:
            stats = get_dashboard_stats()
            self.banner_frame.pack_forget()

            # Update KPI card values
            if "Total Students" in self.kpi_labels:
                self.kpi_labels["Total Students"].config(text=str(stats["total_students"]))
            if "Total Subjects" in self.kpi_labels:
                self.kpi_labels["Total Subjects"].config(text=str(stats["total_subjects"]))
            if "Marks Records" in self.kpi_labels:
                self.kpi_labels["Marks Records"].config(text=str(stats["total_marks_records"]))
            if "Evaluated Students" in self.kpi_labels:
                self.kpi_labels["Evaluated Students"].config(text=str(stats["students_with_marks"]))
            if "Pending Students" in self.kpi_labels:
                self.kpi_labels["Pending Students"].config(text=str(stats["students_without_marks"]))
            if "Overall Average" in self.kpi_labels:
                pct = stats["overall_average_percentage"]
                self.kpi_labels["Overall Average"].config(text=f"{pct:.2f}%")

            # Update recently registered students table
            for row in self.tree_students.get_children():
                self.tree_students.delete(row)

            recent_students = stats.get("recent_students", [])
            if recent_students:
                for s in recent_students:
                    class_div = f"{s.get('class_name', '')} - {s.get('division', '')}"
                    m_count = s.get("marks_count", 0)
                    eval_tag = "status_graded" if m_count > 0 else "status_pending"
                    eval_text = f"✓ Graded ({m_count} subjects)" if m_count > 0 else "⚠️ Pending Marks"

                    self.tree_students.insert("", tk.END, values=(
                        s["student_id"],
                        s["name"],
                        s["roll_no"],
                        class_div,
                        eval_text
                    ), tags=(eval_tag,))
            else:
                self.tree_students.insert("", tk.END, values=("-", "No students registered yet", "-", "-", "-"))

            # Update recent marks table
            for row in self.tree.get_children():
                self.tree.delete(row)

            recent_marks = stats.get("recent_marks", [])
            if recent_marks:
                for r in recent_marks:
                    class_div = f"{r.get('class_name', '')} - {r.get('division', '')}"
                    pct_val = float(r.get('percentage', 0.0))
                    pct_str = f"{pct_val:.2f}%"

                    # Color badge tags
                    if pct_val >= 85.0:
                        tag = "tag_distinction"
                    elif pct_val >= 70.0:
                        tag = "tag_first_class"
                    else:
                        tag = "tag_second_class"

                    self.tree.insert("", tk.END, values=(
                        r["marks_id"],
                        r["roll_no"],
                        r["student_name"],
                        class_div,
                        r["subject_name"],
                        f"{float(r['marks_obtained']):.2f}",
                        r["max_marks"],
                        pct_str
                    ), tags=(tag,))
            else:
                self.tree.insert("", tk.END, values=(
                    "-", "-", "No marks records found in database", "-", "-", "-", "-", "-"
                ))

        except DatabaseConnectionError as ce:
            self._show_banner(f"Database offline: {ce}. Configure PostgreSQL connection in .env or Settings.")
        except DatabaseError as de:
            self._show_banner(f"Database query error: {de}")
        except Exception as e:
            self._show_banner(f"Unexpected error loading dashboard: {e}")

    def _show_banner(self, msg: str):
        """Display an inline alert banner when database is unavailable."""
        self.banner_lbl.config(text=msg)
        self.banner_frame.pack(fill=tk.X, padx=25, pady=(0, 15))
        # Reset card values
        for lbl in self.kpi_labels.values():
            lbl.config(text="--")
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.tree_students.get_children():
            self.tree_students.delete(row)
