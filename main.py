"""
Main Application Entry Point for Internal Marks Management System.
DBMS Micro-Project - Python Tkinter Desktop Application + PostgreSQL.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import get_current_config, update_config
from database import test_connection, get_driver_name

# Import GUI Views
from gui.dashboard import DashboardView
from gui.student_view import StudentView
from gui.subject_view import SubjectView
from gui.marks_view import MarksView
from gui.results_view import ResultsView
from gui.reports_view import ReportsView
from gui.dbms_concepts_view import DBMSConceptsView


class InternalMarksApp(tk.Tk):
    """
    Main Application Window with responsive navigation sidebar,
    ttk design system, database status monitor, and settings modal.
    """

    def __init__(self):
        super().__init__()

        # High-DPI awareness on Windows systems
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.title("Internal Marks Management System — College DBMS Micro-Project")
        self.geometry("1200 Lake" if False else "1280x760")
        self.minsize(1050, 650)

        # Apply application styling
        self._setup_styles()

        # State tracking
        self.current_view_key = "dashboard"
        self.views: Dict[str, ttk.Frame] = {}
        self.nav_buttons: Dict[str, tk.Button] = {}

        # Build interface layout
        self._build_layout()

        # Initialize default view
        self.show_view("dashboard")

        # Non-blocking initial database connectivity check
        self.after(100, self.check_database_status)

    def _setup_styles(self):
        """Configure modern enterprise TTK design tokens and widget styles."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # General frame style
        style.configure("Content.TFrame", background="#F1F5F9")
        style.configure("TFrame", background="#F1F5F9")

        # Typography defaults
        style.configure("TLabel", background="#F1F5F9", foreground="#1E293B", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#0F172A", background="#F1F5F9")
        style.configure("Subheader.TLabel", font=("Segoe UI", 10), foreground="#64748B", background="#F1F5F9")

        # Buttons Palette
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(10, 6))

        # Primary / Accent Button
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), background="#2563EB", foreground="#FFFFFF")
        style.map("Accent.TButton",
                  background=[("pressed", "#1E40AF"), ("active", "#1D4ED8"), ("disabled", "#94A3B8")],
                  foreground=[("disabled", "#F1F5F9")])

        # Success Button (Green - Add / Save)
        style.configure("Success.TButton", font=("Segoe UI", 9, "bold"), background="#16A34A", foreground="#FFFFFF")
        style.map("Success.TButton",
                  background=[("pressed", "#14532D"), ("active", "#15803D"), ("disabled", "#94A3B8")],
                  foreground=[("disabled", "#F1F5F9")])

        # Update Button (Blue - Update Selected)
        style.configure("Update.TButton", font=("Segoe UI", 9, "bold"), background="#0284C7", foreground="#FFFFFF")
        style.map("Update.TButton",
                  background=[("pressed", "#0369A1"), ("active", "#0369A1"), ("disabled", "#94A3B8")],
                  foreground=[("disabled", "#F1F5F9")])

        # Danger Button (Red - Delete Selected)
        style.configure("Danger.TButton", font=("Segoe UI", 9, "bold"), background="#DC2626", foreground="#FFFFFF")
        style.map("Danger.TButton",
                  background=[("pressed", "#991B1B"), ("active", "#B91C1C"), ("disabled", "#94A3B8")],
                  foreground=[("disabled", "#F1F5F9")])

        # Neutral / Clear Button
        style.configure("Clear.TButton", font=("Segoe UI", 9), background="#64748B", foreground="#FFFFFF")
        style.map("Clear.TButton",
                  background=[("pressed", "#334155"), ("active", "#475569"), ("disabled", "#CBD5E1")],
                  foreground=[("disabled", "#F8FAFC")])

        # Treeview styling
        style.configure("Treeview",
                        background="#FFFFFF",
                        foreground="#0F172A",
                        fieldbackground="#FFFFFF",
                        font=("Segoe UI", 9),
                        rowheight=28,
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background="#E2E8F0",
                        foreground="#0F172A",
                        padding=(6, 6))
        style.map("Treeview",
                  background=[("selected", "#DBEAFE")],
                  foreground=[("selected", "#1E3A8A")])

        # Progressbar styling
        style.configure("Green.Horizontal.TProgressbar", foreground="#10B981", background="#10B981", thickness=12)
        style.configure("Blue.Horizontal.TProgressbar", foreground="#3B82F6", background="#3B82F6", thickness=12)
        style.configure("Amber.Horizontal.TProgressbar", foreground="#F59E0B", background="#F59E0B", thickness=12)

        # Notebook tabs
        style.configure("TNotebook", background="#F1F5F9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(16, 8))
        style.map("TNotebook.Tab",
                  background=[("selected", "#FFFFFF"), ("active", "#E2E8F0")],
                  foreground=[("selected", "#2563EB"), ("active", "#1E293B")])

    def _build_layout(self):
        """Construct the two-column layout: Sidebar on left, Content area on right."""
        # Top-level container
        container = ttk.Frame(self, style="Content.TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        # 1. Left Navigation Sidebar
        self.sidebar = tk.Frame(container, bg="#0F172A", width=240)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Brand Title
        brand_frame = tk.Frame(self.sidebar, bg="#0F172A", padx=18, pady=20)
        brand_frame.pack(fill=tk.X)

        brand_lbl = tk.Label(
            brand_frame,
            text="MARKS SYSTEM",
            font=("Segoe UI", 13, "bold"),
            fg="#F8FAFC",
            bg="#0F172A"
        )
        brand_lbl.pack(anchor=tk.W)

        brand_sub = tk.Label(
            brand_frame,
            text="DBMS Micro-Project",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#0F172A"
        )
        brand_sub.pack(anchor=tk.W, pady=(2, 0))

        # Nav separator line
        sep = tk.Frame(self.sidebar, bg="#1E293B", height=1)
        sep.pack(fill=tk.X, padx=12, pady=(0, 10))

        # Nav Buttons
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("students", "👨‍🎓  Students"),
            ("subjects", "📚  Subjects"),
            ("marks", "📝  Marks Entry"),
            ("results", "🎯  Results & Performance"),
            ("reports", "📑  SQL Reports"),
            ("dbms_concepts", "💡  DBMS & Viva Guide")
        ]

        for key, text in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=("Segoe UI", 10),
                fg="#CBD5E1",
                bg="#0F172A",
                activebackground="#1E293B",
                activeforeground="#FFFFFF",
                bd=0,
                anchor=tk.W,
                padx=18,
                pady=10,
                cursor="hand2",
                command=lambda k=key: self.show_view(k)
            )
            btn.pack(fill=tk.X, padx=8, pady=2)
            self.nav_buttons[key] = btn

        # Bottom Sidebar: Settings / Reconnect Button
        side_footer = tk.Frame(self.sidebar, bg="#0F172A", padx=12, pady=15)
        side_footer.pack(side=tk.BOTTOM, fill=tk.X)

        settings_btn = tk.Button(
            side_footer,
            text="⚙️ DB Settings",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#1E293B",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.open_settings_dialog
        )
        settings_btn.pack(fill=tk.X)

        # 2. Main Content Area on Right
        self.content_container = ttk.Frame(container, style="Content.TFrame")
        self.content_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 3. Status Bar at very bottom of window
        self.status_bar = tk.Frame(self, bg="#E2E8F0", height=26, padx=15)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_lbl = tk.Label(
            self.status_bar,
            text="Checking PostgreSQL connection...",
            font=("Segoe UI", 8),
            fg="#475569",
            bg="#E2E8F0"
        )
        self.status_lbl.pack(side=tk.LEFT, pady=3)

        self.driver_lbl = tk.Label(
            self.status_bar,
            text=f"Driver: {get_driver_name() or 'None'}",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#E2E8F0"
        )
        self.driver_lbl.pack(side=tk.RIGHT, pady=3)

        # Instantiate Views lazily or up-front
        self._init_views()

    def _init_views(self):
        """Instantiate views with mutual refresh callbacks."""
        self.views["dashboard"] = DashboardView(self.content_container, navigate_fn=self.show_view)
        self.views["students"] = StudentView(self.content_container, on_data_changed=self.on_database_modified)
        self.views["subjects"] = SubjectView(self.content_container, on_data_changed=self.on_database_modified)
        self.views["marks"] = MarksView(self.content_container, on_data_changed=self.on_database_modified)
        self.views["results"] = ResultsView(self.content_container)
        self.views["reports"] = ReportsView(self.content_container)
        self.views["dbms_concepts"] = DBMSConceptsView(self.content_container)

    def show_view(self, view_key: str):
        """Switch active view and update sidebar highlighting."""
        if view_key not in self.views:
            return

        # Hide currently active view
        if self.current_view_key in self.views:
            self.views[self.current_view_key].pack_forget()

        # Reset button styles
        for k, btn in self.nav_buttons.items():
            if k == view_key:
                btn.config(bg="#2563EB", fg="#FFFFFF", font=("Segoe UI", 10, "bold"))
            else:
                btn.config(bg="#0F172A", fg="#CBD5E1", font=("Segoe UI", 10))

        # Show target view
        self.views[view_key].pack(fill=tk.BOTH, expand=True)
        self.current_view_key = view_key

        # If navigating to a view that requires latest data, trigger refresh
        active_widget = self.views[view_key]
        if hasattr(active_widget, "refresh"):
            active_widget.refresh()
        if hasattr(active_widget, "reload_dropdowns"):
            active_widget.reload_dropdowns()
        if hasattr(active_widget, "reload_options"):
            active_widget.reload_options()
        if hasattr(active_widget, "reload_filters"):
            active_widget.reload_filters()

    def on_database_modified(self):
        """Called whenever an entity is added, updated, or deleted."""
        # Refresh dashboard stats
        if "dashboard" in self.views and hasattr(self.views["dashboard"], "refresh"):
            self.views["dashboard"].refresh()
        # Refresh marks dropdowns if open
        if "marks" in self.views and hasattr(self.views["marks"], "reload_dropdowns"):
            self.views["marks"].reload_dropdowns()
        # Refresh results options if open
        if "results" in self.views and hasattr(self.views["results"], "reload_options"):
            self.views["results"].reload_options()
        # Refresh reports filters if open
        if "reports" in self.views and hasattr(self.views["reports"], "reload_filters"):
            self.views["reports"].reload_filters()

    def check_database_status(self):
        """Check live database connectivity and update status bar text."""
        cfg = get_current_config()
        success, msg = test_connection()
        if success:
            self.status_lbl.config(
                text=f"● Connected: {cfg.display_target} ({msg})",
                fg="#15803D"
            )
        else:
            self.status_lbl.config(
                text=f"● Offline / Disconnected: {cfg.display_target} — Click 'DB Settings' to configure",
                fg="#B91C1C"
            )

    def open_settings_dialog(self):
        """Open Database Connection Settings modal dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("PostgreSQL Database Settings")
        dialog.geometry("460x380")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        cfg = get_current_config()

        pad_f = tk.Frame(dialog, padx=25, pady=20, bg="#FFFFFF")
        pad_f.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad_f, text="Database Connection Settings", font=("Segoe UI", 12, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor=tk.W, pady=(0, 12))

        # Fields
        host_var = tk.StringVar(value=cfg.host)
        port_var = tk.StringVar(value=str(cfg.port))
        db_var = tk.StringVar(value=cfg.database)
        user_var = tk.StringVar(value=cfg.user)
        pass_var = tk.StringVar(value=cfg.password)

        fields = [
            ("Host:", host_var, False),
            ("Port:", port_var, False),
            ("Database Name:", db_var, False),
            ("Username:", user_var, False),
            ("Password:", pass_var, True)
        ]

        entries = {}
        for label, var, is_secret in fields:
            row = tk.Frame(pad_f, bg="#FFFFFF")
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=label, font=("Segoe UI", 9, "bold"), width=15, anchor=tk.W, fg="#334155", bg="#FFFFFF").pack(side=tk.LEFT)
            e = ttk.Entry(row, textvariable=var, show="*" if is_secret else "")
            e.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            entries[label] = e

        status_lbl = tk.Label(pad_f, text="", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF", wraplength=400, justify=tk.LEFT)
        status_lbl.pack(fill=tk.X, pady=(10, 5))

        btn_box = tk.Frame(pad_f, bg="#FFFFFF")
        btn_box.pack(fill=tk.X, pady=(10, 0))

        def on_test():
            try:
                p = int(port_var.get().strip())
            except ValueError:
                status_lbl.config(text="Port must be a valid integer.", fg="#B91C1C")
                return

            temp_cfg = update_config(
                host=host_var.get(),
                port=p,
                database=db_var.get(),
                user=user_var.get(),
                password=pass_var.get(),
                persist_to_env=False
            )
            success, msg = test_connection(temp_cfg)
            if success:
                status_lbl.config(text=f"Connection successful: {msg}", fg="#15803D")
            else:
                status_lbl.config(text=f"Connection failed: {msg}", fg="#B91C1C")

        def on_save():
            try:
                p = int(port_var.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Port must be an integer.")
                return

            update_config(
                host=host_var.get(),
                port=p,
                database=db_var.get(),
                user=user_var.get(),
                password=pass_var.get(),
                persist_to_env=True
            )
            self.check_database_status()
            self.on_database_modified()
            messagebox.showinfo("Saved", "Settings saved successfully to .env and active runtime.")
            dialog.destroy()

        test_btn = ttk.Button(btn_box, text="Test Connection", command=on_test)
        test_btn.pack(side=tk.LEFT, padx=(0, 8))

        save_btn = ttk.Button(btn_box, text="Save & Connect", style="Accent.TButton", command=on_save)
        save_btn.pack(side=tk.RIGHT)

        cancel_btn = ttk.Button(btn_box, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=8)


def main():
    """Application bootstrap."""
    app = InternalMarksApp()
    app.mainloop()


if __name__ == "__main__":
    main()
