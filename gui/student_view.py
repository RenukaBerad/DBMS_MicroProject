"""
Student Management View Module.
Provides CRUD interface for STUDENT records with search, validation,
and integrity constraint handling.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from services.student_service import (
    add_student,
    get_all_students,
    get_student_by_id,
    update_student,
    delete_student
)
from database import DatabaseIntegrityError, DatabaseConnectionError, DatabaseError


class StudentView(ttk.Frame):
    """
    Student CRUD management interface with split form and data table.
    """

    def __init__(self, parent: tk.Widget, on_data_changed: Optional[Callable[[], None]] = None):
        super().__init__(parent, style="Content.TFrame")
        self.on_data_changed = on_data_changed
        self.selected_student_id: Optional[int] = None

        self._build_ui()

    def _build_ui(self):
        # 1. Header & Search Bar
        header = ttk.Frame(self, style="Content.TFrame")
        header.pack(fill=tk.X, padx=25, pady=(20, 10))

        title_box = ttk.Frame(header, style="Content.TFrame")
        title_box.pack(side=tk.LEFT)

        title_lbl = ttk.Label(
            title_box,
            text="Student Management",
            font=("Segoe UI", 18, "bold"),
            foreground="#0F172A",
            background="#F8FAFC"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            title_box,
            text="Manage student profiles (Mapped to conceptual ER Entity: STUDENT)",
            font=("Segoe UI", 10),
            foreground="#64748B",
            background="#F8FAFC"
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Search Box
        search_box = ttk.Frame(header, style="Content.TFrame")
        search_box.pack(side=tk.RIGHT, pady=5)

        ttk.Label(search_box, text="Search:", font=("Segoe UI", 9, "bold"), background="#F8FAFC").pack(side=tk.LEFT, padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_box, textvariable=self.search_var, width=22)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.search_entry.bind("<Return>", lambda e: self.search_students())

        search_btn = ttk.Button(search_box, text="Search", command=self.search_students)
        search_btn.pack(side=tk.LEFT, padx=(0, 4))

        clear_search_btn = ttk.Button(search_box, text="Clear", command=self.clear_search)
        clear_search_btn.pack(side=tk.LEFT)

        # 2. Main Split Area: Left Form / Right Table
        main_paned = ttk.Frame(self, style="Content.TFrame")
        main_paned.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        # Left Form Card
        form_card_border = tk.Frame(main_paned, bg="#E2E8F0", bd=1)
        form_card_border.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=(0, 15))

        form_card = tk.Frame(form_card_border, bg="#FFFFFF", padx=20, pady=20, width=320)
        form_card.pack(fill=tk.BOTH, expand=True)
        form_card.pack_propagate(False)

        form_title = tk.Label(
            form_card,
            text="Student Details",
            font=("Segoe UI", 13, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        )
        form_title.pack(anchor=tk.W, pady=(0, 12))

        # Form Fields
        self.id_var = tk.StringVar(value="")
        self.name_var = tk.StringVar()
        self.roll_var = tk.StringVar()
        self.class_var = tk.StringVar(value="TE-COMP")
        self.div_var = tk.StringVar(value="A")

        # Field: Student ID (Optional for custom ID or auto-generated)
        id_lbl = tk.Label(form_card, text="Student ID (Auto if blank):", font=("Segoe UI", 9), fg="#475569", bg="#FFFFFF")
        id_lbl.pack(anchor=tk.W)
        self.id_entry = ttk.Entry(form_card, textvariable=self.id_var)
        self.id_entry.pack(fill=tk.X, pady=(2, 10))

        # Field: Full Name
        name_lbl = tk.Label(form_card, text="Student Full Name *:", font=("Segoe UI", 9, "bold"), fg="#1E293B", bg="#FFFFFF")
        name_lbl.pack(anchor=tk.W)
        self.name_entry = ttk.Entry(form_card, textvariable=self.name_var)
        self.name_entry.pack(fill=tk.X, pady=(2, 10))

        # Field: Roll No
        roll_lbl = tk.Label(form_card, text="Roll Number *:", font=("Segoe UI", 9, "bold"), fg="#1E293B", bg="#FFFFFF")
        roll_lbl.pack(anchor=tk.W)
        self.roll_entry = ttk.Entry(form_card, textvariable=self.roll_var)
        self.roll_entry.pack(fill=tk.X, pady=(2, 10))

        # Field: Class (maps to ER attribute class)
        class_lbl = tk.Label(form_card, text="Class (e.g. TE-COMP) *:", font=("Segoe UI", 9, "bold"), fg="#1E293B", bg="#FFFFFF")
        class_lbl.pack(anchor=tk.W)
        self.class_combo = ttk.Combobox(form_card, textvariable=self.class_var, values=["FE-COMP", "SE-COMP", "TE-COMP", "BE-COMP"])
        self.class_combo.pack(fill=tk.X, pady=(2, 10))

        # Field: Division
        div_lbl = tk.Label(form_card, text="Division *:", font=("Segoe UI", 9, "bold"), fg="#1E293B", bg="#FFFFFF")
        div_lbl.pack(anchor=tk.W)
        self.div_combo = ttk.Combobox(form_card, textvariable=self.div_var, values=["A", "B", "C", "D"])
        self.div_combo.pack(fill=tk.X, pady=(2, 15))

        # Buttons Frame
        btn_box = tk.Frame(form_card, bg="#FFFFFF")
        btn_box.pack(fill=tk.X, pady=(5, 0))

        self.save_btn = ttk.Button(btn_box, text="💾 Save Student", style="Success.TButton", command=self.save_student)
        self.save_btn.pack(fill=tk.X, pady=(0, 6))

        self.update_btn = ttk.Button(btn_box, text="✏️ Update Selected", style="Update.TButton", command=self.update_student_action, state=tk.DISABLED)
        self.update_btn.pack(fill=tk.X, pady=(0, 6))

        self.delete_btn = ttk.Button(btn_box, text="🗑️ Delete Selected", style="Danger.TButton", command=self.delete_student_action, state=tk.DISABLED)
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

        cols = ("id", "name", "roll", "class_name", "div")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="Student ID")
        self.tree.heading("name", text="Full Name")
        self.tree.heading("roll", text="Roll No")
        self.tree.heading("class_name", text="Class")
        self.tree.heading("div", text="Division")

        self.tree.column("id", width=80, anchor=tk.CENTER)
        self.tree.column("name", width=220, anchor=tk.W)
        self.tree.column("roll", width=100, anchor=tk.CENTER)
        self.tree.column("class_name", width=120, anchor=tk.CENTER)
        self.tree.column("div", width=90, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Alternating row tags
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F8FAFC")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def on_tree_select(self, event=None):
        """Populate form fields when a table row is selected."""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        vals = item["values"]
        if not vals or vals[0] == "-":
            return

        self.selected_student_id = int(vals[0])
        self.id_var.set(str(vals[0]))
        self.name_var.set(str(vals[1]))
        self.roll_var.set(str(vals[2]))
        self.class_var.set(str(vals[3]))
        self.div_var.set(str(vals[4]))
        self.form_msg_lbl.config(text="")

        self.id_entry.config(state="disabled")
        self.save_btn.config(state=tk.DISABLED)
        self.update_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)

    def clear_form(self):
        """Reset the form to fresh entry state."""
        self.selected_student_id = None
        self.id_var.set("")
        self.name_var.set("")
        self.roll_var.set("")
        self.class_var.set("TE-COMP")
        self.div_var.set("A")
        self.form_msg_lbl.config(text="")

        self.id_entry.config(state="normal")
        self.save_btn.config(state=tk.NORMAL)
        self.update_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def save_student(self):
        """Handle Add Student button click."""
        self.form_msg_lbl.config(text="")
        try:
            custom_id = int(self.id_var.get().strip()) if self.id_var.get().strip() else None
        except ValueError:
            msg = "Student ID must be a numeric integer if specified."
            self.form_msg_lbl.config(text=f"⚠️ {msg}", fg="#DC2626")
            messagebox.showerror("Validation Error", msg, parent=self)
            return

        try:
            new_id = add_student(
                name=self.name_var.get(),
                roll_no=self.roll_var.get(),
                class_name=self.class_var.get(),
                division=self.div_var.get(),
                student_id=custom_id
            )
            success_msg = f"✓ Student successfully saved with ID: {new_id}"
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

    def update_student_action(self):
        """Handle Update Selected button click."""
        self.form_msg_lbl.config(text="")
        if not self.selected_student_id:
            msg = "Please select a student from the table to update."
            self.form_msg_lbl.config(text=f"⚠️ {msg}", fg="#D97706")
            messagebox.showwarning("Selection Required", msg, parent=self)
            return

        try:
            success = update_student(
                student_id=self.selected_student_id,
                name=self.name_var.get(),
                roll_no=self.roll_var.get(),
                class_name=self.class_var.get(),
                division=self.div_var.get()
            )
            if success:
                success_msg = "✓ Student profile updated successfully in PostgreSQL."
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

    def delete_student_action(self):
        """Handle Delete Selected button click with confirmation."""
        self.form_msg_lbl.config(text="")
        if not self.selected_student_id:
            msg = "Please select a student from the table to delete."
            self.form_msg_lbl.config(text=f"⚠️ {msg}", fg="#D97706")
            messagebox.showwarning("Selection Required", msg, parent=self)
            return

        student_name = self.name_var.get()
        confirm = messagebox.askyesno(
            "Confirm Student Deletion",
            f"Are you sure you want to delete student:\n\n"
            f"ID: {self.selected_student_id}\nName: {student_name}\n\n"
            "Note: Deletion will be rejected if marks records exist for this student.",
            icon="warning",
            parent=self
        )
        if not confirm:
            return

        try:
            success = delete_student(self.selected_student_id)
            if success:
                success_msg = "✓ Student record successfully deleted."
                self.form_msg_lbl.config(text=success_msg, fg="#16A34A")
                messagebox.showinfo("Deleted", success_msg, parent=self)
                self.clear_form()
                self.refresh()
                if self.on_data_changed:
                    self.on_data_changed()
        except DatabaseIntegrityError as die:
            self.form_msg_lbl.config(text=f"✕ {die}", fg="#DC2626")
            messagebox.showerror("Referential Integrity Protection", str(die), parent=self)
        except DatabaseError as de:
            self.form_msg_lbl.config(text=f"✕ {de}", fg="#DC2626")
            messagebox.showerror("Database Error", str(de), parent=self)

    def search_students(self):
        """Execute search query against PostgreSQL."""
        self.refresh(search_query=self.search_var.get())

    def clear_search(self):
        """Reset search filter."""
        self.search_var.set("")
        self.refresh()

    def refresh(self, search_query: Optional[str] = None):
        """Reload students from PostgreSQL into the treeview."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            students = get_all_students(search_query=search_query)
            if students:
                for idx, s in enumerate(students):
                    row_tag = "evenrow" if idx % 2 == 0 else "oddrow"
                    self.tree.insert("", tk.END, values=(
                        s["student_id"],
                        s["name"],
                        s["roll_no"],
                        s["class_name"],
                        s["division"]
                    ), tags=(row_tag,))
            else:
                self.tree.insert("", tk.END, values=("-", "No matching student records found", "-", "-", "-"))
        except DatabaseConnectionError:
            self.tree.insert("", tk.END, values=("-", "Database offline - Check connection settings", "-", "-", "-"))
        except DatabaseError as de:
            self.tree.insert("", tk.END, values=("-", f"Error loading records: {de}", "-", "-", "-"))
