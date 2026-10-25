"""
Marks Management View Module.
Provides CRUD interface for the associative MARKS entity,
including student/subject comboboxes, range validation, search/filtering,
and foreign key integrity preservation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List
from services.marks_service import (
    add_marks,
    get_all_marks,
    get_marks_by_id,
    update_marks,
    delete_marks,
    get_student_dropdown_options,
    get_subject_dropdown_options
)
from services.student_service import get_distinct_classes_and_divisions
from database import DatabaseIntegrityError, DatabaseConnectionError, DatabaseError


class MarksView(ttk.Frame):
    """
    Marks CRUD management view linking students and subjects.
    """

    def __init__(self, parent: tk.Widget, on_data_changed: Optional[Callable[[], None]] = None):
        super().__init__(parent, style="Content.TFrame")
        self.on_data_changed = on_data_changed
        self.selected_marks_id: Optional[int] = None

        self.student_options: List[Dict[str, Any]] = []
        self.subject_options: List[Dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self):
        # 1. Header
        header = ttk.Frame(self, style="Content.TFrame")
        header.pack(fill=tk.X, padx=25, pady=(20, 10))

        title_box = ttk.Frame(header, style="Content.TFrame")
        title_box.pack(side=tk.LEFT)

        title_lbl = ttk.Label(
            title_box,
            text="Marks Entry & Management",
            font=("Segoe UI", 18, "bold"),
            foreground="#0F172A",
            background="#F8FAFC"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            title_box,
            text="Associative entity resolving M:N relationship between Student and Subject",
            font=("Segoe UI", 10),
            foreground="#64748B",
            background="#F8FAFC"
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # 2. Filter Bar
        filter_bar = ttk.Frame(self, style="Content.TFrame")
        filter_bar.pack(fill=tk.X, padx=25, pady=(0, 10))

        # Filter: Class
        ttk.Label(filter_bar, text="Class:", font=("Segoe UI", 9, "bold"), background="#F8FAFC").pack(side=tk.LEFT, padx=(0, 4))
        self.class_filter_var = tk.StringVar(value="ALL")
        self.class_combo = ttk.Combobox(filter_bar, textvariable=self.class_filter_var, state="readonly", width=12)
        self.class_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.class_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Filter: Division
        ttk.Label(filter_bar, text="Div:", font=("Segoe UI", 9, "bold"), background="#F8FAFC").pack(side=tk.LEFT, padx=(0, 4))
        self.div_filter_var = tk.StringVar(value="ALL")
        self.div_combo = ttk.Combobox(filter_bar, textvariable=self.div_filter_var, state="readonly", width=8)
        self.div_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.div_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Filter: Subject
        ttk.Label(filter_bar, text="Subject:", font=("Segoe UI", 9, "bold"), background="#F8FAFC").pack(side=tk.LEFT, padx=(0, 4))
        self.subject_filter_var = tk.StringVar(value="ALL")
        self.subject_filter_combo = ttk.Combobox(filter_bar, textvariable=self.subject_filter_var, state="readonly", width=22)
        self.subject_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.subject_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Search box
        ttk.Label(filter_bar, text="Search:", font=("Segoe UI", 9, "bold"), background="#F8FAFC").pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_bar, textvariable=self.search_var, width=16)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.search_entry.bind("<Return>", lambda e: self.apply_filters())

        filter_btn = ttk.Button(filter_bar, text="Filter", command=self.apply_filters)
        filter_btn.pack(side=tk.LEFT, padx=(0, 4))

        reset_btn = ttk.Button(filter_bar, text="Reset", command=self.reset_filters)
        reset_btn.pack(side=tk.LEFT)

        # 3. Main Split Area: Left Form / Right Table
        main_paned = ttk.Frame(self, style="Content.TFrame")
        main_paned.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        # Left Form Card
        form_card_border = tk.Frame(main_paned, bg="#E2E8F0", bd=1)
        form_card_border.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=(0, 15))

        form_card = tk.Frame(form_card_border, bg="#FFFFFF", padx=20, pady=20, width=340)
        form_card.pack(fill=tk.BOTH, expand=True)
        form_card.pack_propagate(False)

        form_title = tk.Label(
            form_card,
            text="Marks Entry Form",
            font=("Segoe UI", 13, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        )
        form_title.pack(anchor=tk.W, pady=(0, 12))

        # Student Combobox
        student_lbl = tk.Label(form_card, text="Select Student (FK: student_id) *:", font=("Segoe UI", 9, "bold"), fg="#1E293B", bg="#FFFFFF")
        student_lbl.pack(anchor=tk.W)
        self.student_combo_var = tk.StringVar()
        self.student_combo = ttk.Combobox(form_card, textvariable=self.student_combo_var, state="readonly")
        self.student_combo.pack(fill=tk.X, pady=(2, 10))

        # Subject Combobox
        subject_lbl = tk.Label(form_card, text="Select Subject (FK: subject_id) *:", font=("Segoe UI", 9, "bold"), fg="#1E293B", bg="#FFFFFF")
        subject_lbl.pack(anchor=tk.W)
        self.subject_combo_var = tk.StringVar()
        self.subject_combo = ttk.Combobox(form_card, textvariable=self.subject_combo_var, state="readonly")
        self.subject_combo.pack(fill=tk.X, pady=(2, 4))
        self.subject_combo.bind("<<ComboboxSelected>>", self.on_form_subject_change)

        # Max marks reminder pill
        self.max_marks_hint = tk.Label(
            form_card,
            text="Subject maximum: --",
            font=("Segoe UI", 8, "italic"),
            fg="#2563EB",
            bg="#EFF6FF",
            padx=6,
            pady=2
        )
        self.max_marks_hint.pack(anchor=tk.W, pady=(0, 10))

        # Marks Obtained Entry
        marks_lbl = tk.Label(form_card, text="Marks Obtained (0 <= marks <= max) *:", font=("Segoe UI", 9, "bold"), fg="#1E293B", bg="#FFFFFF")
        marks_lbl.pack(anchor=tk.W)
        self.marks_obtained_var = tk.StringVar()
        self.marks_entry = ttk.Entry(form_card, textvariable=self.marks_obtained_var)
        self.marks_entry.pack(fill=tk.X, pady=(2, 15))

        # Buttons Frame
        btn_box = tk.Frame(form_card, bg="#FFFFFF")
        btn_box.pack(fill=tk.X, pady=(5, 0))

        self.save_btn = ttk.Button(btn_box, text="💾 Save Marks Record", style="Success.TButton", command=self.save_marks)
        self.save_btn.pack(fill=tk.X, pady=(0, 6))

        self.update_btn = ttk.Button(btn_box, text="✏️ Update Score", style="Update.TButton", command=self.update_marks_action, state=tk.DISABLED)
        self.update_btn.pack(fill=tk.X, pady=(0, 6))

        self.delete_btn = ttk.Button(btn_box, text="🗑️ Delete Marks Record", style="Danger.TButton", command=self.delete_marks_action, state=tk.DISABLED)
        self.delete_btn.pack(fill=tk.X, pady=(0, 6))

        self.clear_btn = ttk.Button(btn_box, text="🧹 Clear Form", style="Clear.TButton", command=self.clear_form)
        self.clear_btn.pack(fill=tk.X)

        # Inline Form Feedback Label
        self.form_msg_lbl = tk.Label(
            form_card,
            text="",
            font=("Segoe UI", 8),
            wraplength=280,
            bg="#FFFFFF",
            justify=tk.LEFT
        )
        self.form_msg_lbl.pack(fill=tk.X, pady=(8, 0))

        # Right Table
        table_container = ttk.Frame(main_paned)
        table_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=(0, 15))

        cols = ("id", "roll", "name", "class_div", "subject", "score", "max", "pct")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="Marks ID")
        self.tree.heading("roll", text="Roll No")
        self.tree.heading("name", text="Student Name")
        self.tree.heading("class_div", text="Class & Div")
        self.tree.heading("subject", text="Subject")
        self.tree.heading("score", text="Marks Obtained")
        self.tree.heading("max", text="Max Marks")
        self.tree.heading("pct", text="Percentage")

        self.tree.column("id", width=65, anchor=tk.CENTER)
        self.tree.column("roll", width=75, anchor=tk.CENTER)
        self.tree.column("name", width=170, anchor=tk.W)
        self.tree.column("class_div", width=100, anchor=tk.CENTER)
        self.tree.column("subject", width=200, anchor=tk.W)
        self.tree.column("score", width=105, anchor=tk.E)
        self.tree.column("max", width=85, anchor=tk.E)
        self.tree.column("pct", width=95, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Percentage color tags
        self.tree.tag_configure("tag_distinction", background="#F0FDF4", foreground="#166534")  # >= 85%
        self.tree.tag_configure("tag_first_class", background="#EFF6FF", foreground="#1E40AF")   # 70 - 84.99%
        self.tree.tag_configure("tag_second_class", background="#FFFBEB", foreground="#92400E")  # < 70%

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def reload_dropdowns(self):
        """Fetch fresh student and subject lists for dropdowns."""
        try:
            self.student_options = get_student_dropdown_options()
            student_labels = [s["display"] for s in self.student_options]
            self.student_combo["values"] = student_labels

            self.subject_options = get_subject_dropdown_options()
            subject_labels = [sub["display"] for sub in self.subject_options]
            self.subject_combo["values"] = subject_labels

            # Reload filter dropdowns
            classes, divs = get_distinct_classes_and_divisions()
            self.class_combo["values"] = ["ALL"] + classes
            self.div_combo["values"] = ["ALL"] + divs
            self.subject_filter_combo["values"] = ["ALL"] + [sub["subject_name"] for sub in self.subject_options]

        except Exception:
            pass

    def on_form_subject_change(self, event=None):
        """Update max marks hint label when subject selection changes."""
        idx = self.subject_combo.current()
        if idx >= 0 and idx < len(self.subject_options):
            sub = self.subject_options[idx]
            self.max_marks_hint.config(text=f"Subject maximum: {sub['max_marks']} marks")
        else:
            self.max_marks_hint.config(text="Subject maximum: --")

    def on_tree_select(self, event=None):
        """Populate form when selecting a row in treeview."""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        vals = item["values"]
        if not vals or vals[0] == "-":
            return

        self.selected_marks_id = int(vals[0])
        marks_rec = get_marks_by_id(self.selected_marks_id)
        if not marks_rec:
            return

        # Select student in combo
        for i, s in enumerate(self.student_options):
            if s["student_id"] == marks_rec["student_id"]:
                self.student_combo.current(i)
                break

        # Select subject in combo
        for i, sub in enumerate(self.subject_options):
            if sub["subject_id"] == marks_rec["subject_id"]:
                self.subject_combo.current(i)
                self.max_marks_hint.config(text=f"Subject maximum: {sub['max_marks']} marks")
                break

        self.marks_obtained_var.set(str(marks_rec["marks_obtained"]))
        self.form_msg_lbl.config(text="")

        # For update, lock student and subject foreign keys to preserve integrity
        self.student_combo.config(state="disabled")
        self.subject_combo.config(state="disabled")
        self.save_btn.config(state=tk.DISABLED)
        self.update_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)

    def clear_form(self):
        """Reset form fields."""
        self.selected_marks_id = None
        self.student_combo_var.set("")
        self.subject_combo_var.set("")
        self.marks_obtained_var.set("")
        self.max_marks_hint.config(text="Subject maximum: --")
        self.form_msg_lbl.config(text="")

        self.student_combo.config(state="readonly")
        self.subject_combo.config(state="readonly")
        self.save_btn.config(state=tk.NORMAL)
        self.update_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def save_marks(self):
        """Handle Add Marks action."""
        self.form_msg_lbl.config(text="")
        s_idx = self.student_combo.current()
        sub_idx = self.subject_combo.current()

        if s_idx < 0:
            msg = "Please select a Student from the dropdown."
            self.form_msg_lbl.config(text=f"⚠️ {msg}", fg="#D97706")
            messagebox.showwarning("Validation Error", msg, parent=self)
            return
        if sub_idx < 0:
            msg = "Please select a Subject from the dropdown."
            self.form_msg_lbl.config(text=f"⚠️ {msg}", fg="#D97706")
            messagebox.showwarning("Validation Error", msg, parent=self)
            return

        student_id = self.student_options[s_idx]["student_id"]
        subject_id = self.subject_options[sub_idx]["subject_id"]

        try:
            marks_id = add_marks(
                student_id=student_id,
                subject_id=subject_id,
                marks_obtained=self.marks_obtained_var.get()
            )
            success_msg = f"✓ Marks record successfully created with ID: {marks_id}"
            self.form_msg_lbl.config(text=success_msg, fg="#16A34A")
            messagebox.showinfo("Success", success_msg, parent=self)
            self.clear_form()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
        except ValueError as ve:
            self.form_msg_lbl.config(text=f"⚠️ {ve}", fg="#D97706")
            messagebox.showwarning("Validation Warning", str(ve), parent=self)
        except DatabaseIntegrityError as die:
            self.form_msg_lbl.config(text=f"✕ {die}", fg="#DC2626")
            messagebox.showerror("Integrity Error", str(die), parent=self)
        except DatabaseError as de:
            self.form_msg_lbl.config(text=f"✕ {de}", fg="#DC2626")
            messagebox.showerror("Database Error", str(de), parent=self)

    def update_marks_action(self):
        """Handle Update Marks action."""
        self.form_msg_lbl.config(text="")
        if not self.selected_marks_id:
            msg = "Please select a marks record from the table to update."
            self.form_msg_lbl.config(text=f"⚠️ {msg}", fg="#D97706")
            messagebox.showwarning("Selection Required", msg, parent=self)
            return

        try:
            success = update_marks(
                marks_id=self.selected_marks_id,
                marks_obtained=self.marks_obtained_var.get()
            )
            if success:
                success_msg = "✓ Marks obtained score updated successfully in PostgreSQL."
                self.form_msg_lbl.config(text=success_msg, fg="#16A34A")
                messagebox.showinfo("Updated", success_msg, parent=self)
                self.clear_form()
                self.refresh()
                if self.on_data_changed:
                    self.on_data_changed()
            else:
                self.form_msg_lbl.config(text="No changes were applied.", fg="#64748B")
        except ValueError as ve:
            self.form_msg_lbl.config(text=f"⚠️ {ve}", fg="#D97706")
            messagebox.showwarning("Validation Warning", str(ve), parent=self)
        except DatabaseIntegrityError as die:
            self.form_msg_lbl.config(text=f"✕ {die}", fg="#DC2626")
            messagebox.showerror("Integrity Error", str(die), parent=self)
        except DatabaseError as de:
            self.form_msg_lbl.config(text=f"✕ {de}", fg="#DC2626")
            messagebox.showerror("Database Error", str(de), parent=self)

    def delete_marks_action(self):
        """Handle Delete Marks action."""
        self.form_msg_lbl.config(text="")
        if not self.selected_marks_id:
            msg = "Please select a marks record to delete."
            self.form_msg_lbl.config(text=f"⚠️ {msg}", fg="#D97706")
            messagebox.showwarning("Selection Required", msg, parent=self)
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete marks record #{self.selected_marks_id}?",
            icon="warning",
            parent=self
        )
        if not confirm:
            return

        try:
            success = delete_marks(self.selected_marks_id)
            if success:
                success_msg = "✓ Marks record deleted successfully."
                self.form_msg_lbl.config(text=success_msg, fg="#16A34A")
                messagebox.showinfo("Deleted", success_msg, parent=self)
                self.clear_form()
                self.refresh()
                if self.on_data_changed:
                    self.on_data_changed()
        except DatabaseError as de:
            self.form_msg_lbl.config(text=f"✕ {de}", fg="#DC2626")
            messagebox.showerror("Database Error", str(de), parent=self)

    def apply_filters(self):
        """Apply active filters and reload treeview."""
        class_val = self.class_filter_var.get()
        div_val = self.div_filter_var.get()

        sub_id = None
        sub_name = self.subject_filter_var.get()
        if sub_name != "ALL":
            for sub in self.subject_options:
                if sub["subject_name"] == sub_name:
                    sub_id = sub["subject_id"]
                    break

        self.refresh(
            class_filter=class_val,
            division_filter=div_val,
            subject_id_filter=sub_id,
            search_query=self.search_var.get()
        )

    def reset_filters(self):
        """Reset all filter controls."""
        self.class_filter_var.set("ALL")
        self.div_filter_var.set("ALL")
        self.subject_filter_var.set("ALL")
        self.search_var.set("")
        self.refresh()

    def refresh(
        self,
        class_filter: Optional[str] = None,
        division_filter: Optional[str] = None,
        subject_id_filter: Optional[int] = None,
        search_query: Optional[str] = None
    ):
        """Reload marks from PostgreSQL into the treeview."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            records = get_all_marks(
                class_filter=class_filter,
                division_filter=division_filter,
                subject_id_filter=subject_id_filter,
                search_query=search_query
            )
            if records:
                for r in records:
                    class_div = f"{r.get('class_name', '')} - {r.get('division', '')}"
                    pct_val = float(r.get('percentage', 0.0))
                    pct_str = f"{pct_val:.2f}%"

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
                self.tree.insert("", tk.END, values=("-", "-", "No matching marks records found", "-", "-", "-", "-", "-"))
        except DatabaseConnectionError:
            self.tree.insert("", tk.END, values=("-", "-", "Database offline - Check connection", "-", "-", "-", "-", "-"))
        except DatabaseError as de:
            self.tree.insert("", tk.END, values=("-", "-", f"Error: {de}", "-", "-", "-", "-", "-"))
