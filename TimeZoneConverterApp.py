import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pytz
from tzlocal import get_localzone
from tkcalendar import Calendar
from preferences import PreferencesManager

# pyinstaller --hidden-import babel.numbers --onefile .\TimeZoneConverterApp.py


# ---------------------------------------------------------------------------
# Searchable Timezone Picker Popup
# ---------------------------------------------------------------------------

class SearchableTimezoneDropdown(tk.Toplevel):
    """Popup with a live-filtered listbox over all pytz timezones."""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Select Timezone")
        self.resizable(False, False)
        self.grab_set()
        self.callback = callback
        self.all_timezones = sorted(pytz.all_timezones)

        # ── Search bar ──────────────────────────────────────────────────────
        search_frame = ttk.Frame(self, padding=(10, 10, 10, 4))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter)
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=38)
        entry.pack(side="left", padx=(6, 0))
        entry.focus_set()

        # ── Listbox ─────────────────────────────────────────────────────────
        list_frame = ttk.Frame(self, padding=(10, 0, 10, 0))
        list_frame.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical")
        sb.pack(side="right", fill="y")
        self.listbox = tk.Listbox(list_frame, yscrollcommand=sb.set, width=44, height=16,
                                  font=("Arial", 10))
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=self.listbox.yview)
        self._populate(self.all_timezones)
        self.listbox.bind("<Double-Button-1>", lambda _e: self._select())

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Select", command=self._select).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=4)

    def _populate(self, timezones):
        self.listbox.delete(0, tk.END)
        for tz in timezones:
            self.listbox.insert(tk.END, tz)

    def _filter(self, *_):
        q = self.search_var.get().lower()
        self._populate([tz for tz in self.all_timezones if q in tz.lower()])

    def _select(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a timezone first.", parent=self)
            return
        self.callback(self.listbox.get(sel[0]))
        self.destroy()


# ---------------------------------------------------------------------------
# Add / Edit Timezone Dialog
# ---------------------------------------------------------------------------

class AddEditTimezoneDialog(tk.Toplevel):
    """Dialog for adding a new timezone or editing an existing one."""

    def __init__(self, parent, prefs_manager, on_save, edit_data=None):
        """
        edit_data: (location_name, tz_id) tuple when editing; None when adding.
        on_save: zero-argument callback called after a successful save.
        """
        super().__init__(parent)
        self.title("Edit Timezone" if edit_data else "Add Timezone")
        self.resizable(False, False)
        self.grab_set()
        self.prefs_manager = prefs_manager
        self.on_save = on_save
        self.edit_data = edit_data

        self.selected_tz = tk.StringVar(value=edit_data[1] if edit_data else "")
        self.name_var = tk.StringVar(value=edit_data[0] if edit_data else "")

        pad = {"padx": 12, "pady": 8}

        # ── Location name ────────────────────────────────────────────────────
        ttk.Label(self, text="Location Name:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.name_var, width=28).grid(row=0, column=1, **pad)

        # ── Timezone ID with Browse button ───────────────────────────────────
        ttk.Label(self, text="Timezone ID:").grid(row=1, column=0, sticky="w", **pad)
        tz_frame = ttk.Frame(self)
        tz_frame.grid(row=1, column=1, **pad)
        ttk.Label(tz_frame, textvariable=self.selected_tz, width=26,
                  relief="sunken", anchor="w").pack(side="left")
        ttk.Button(tz_frame, text="Browse…", command=self._browse_tz).pack(side="left", padx=(6, 0))

        # ── Action buttons ───────────────────────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(4, 14))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def _browse_tz(self):
        SearchableTimezoneDropdown(self, lambda tz: self.selected_tz.set(tz))

    def _save(self):
        name = self.name_var.get().strip()
        tz_id = self.selected_tz.get().strip()

        if not name:
            messagebox.showerror("Error", "Location name cannot be empty.", parent=self)
            return
        if not tz_id:
            messagebox.showerror("Error", "Please select a timezone by clicking Browse…", parent=self)
            return
        try:
            pytz.timezone(tz_id)
        except pytz.exceptions.UnknownTimeZoneError:
            messagebox.showerror("Error", f"Unknown timezone ID: {tz_id}", parent=self)
            return

        # If renaming, remove old key first
        if self.edit_data and self.edit_data[0] != name:
            self.prefs_manager.delete_custom_timezone(self.edit_data[0])

        self.prefs_manager.add_custom_timezone(name, tz_id)
        self.on_save()
        self.destroy()


# ---------------------------------------------------------------------------
# Preferences Dialog
# ---------------------------------------------------------------------------

class PreferencesDialog(tk.Toplevel):
    """
    Shows all configured timezones in a table with live current time,
    date, and offset from local.  Supports Add / Edit / Delete.
    """

    COLUMNS = ("location", "tz_id", "cur_time", "cur_date", "offset")
    HEADINGS = ("Location", "TZ ID", "Current Time", "Current Date", "Offset (from local)")
    WIDTHS   = (140, 200, 110, 110, 150)

    def __init__(self, parent, prefs_manager):
        super().__init__(parent)
        self.title("Preferences – Timezone Configuration")
        self.grab_set()
        self.minsize(760, 380)
        self.prefs_manager = prefs_manager
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = ttk.Frame(self, padding=(10, 10, 10, 4))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="➕  Add",    command=self._add).pack(side="left", padx=3)
        ttk.Button(toolbar, text="✏️  Edit",   command=self._edit).pack(side="left", padx=3)
        ttk.Button(toolbar, text="🗑  Delete", command=self._delete).pack(side="left", padx=3)
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_table).pack(side="left", padx=3)

        # ── Treeview ─────────────────────────────────────────────────────────
        tree_frame = ttk.Frame(self, padding=(10, 0, 10, 0))
        tree_frame.pack(fill="both", expand=True)

        sb = ttk.Scrollbar(tree_frame, orient="vertical")
        sb.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.COLUMNS,
            show="headings",
            yscrollcommand=sb.set,
            selectmode="browse",
        )
        sb.config(command=self.tree.yview)

        for col, heading, width in zip(self.COLUMNS, self.HEADINGS, self.WIDTHS):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=60, anchor="w")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-Button-1>", lambda _e: self._edit())

        # ── Footer ───────────────────────────────────────────────────────────
        footer = ttk.Frame(self, padding=10)
        footer.pack()
        ttk.Button(footer, text="Close", command=self.destroy).pack()

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        now_utc = datetime.now(pytz.utc)
        local_tz = get_localzone()
        local_offset = now_utc.astimezone(local_tz).utcoffset()

        for location, tz_id in self.prefs_manager.custom_timezones.items():
            try:
                tz = pytz.timezone(tz_id)
                now_here = now_utc.astimezone(tz)
                diff_secs = int((now_here.utcoffset() - local_offset).total_seconds())
                hrs, rem = divmod(abs(diff_secs), 3600)
                mins = rem // 60
                sign = "+" if diff_secs >= 0 else "−"
                offset_str = f"{sign}{hrs:02d}h {mins:02d}m"
                self.tree.insert("", "end", values=(
                    location,
                    tz_id,
                    now_here.strftime("%H:%M"),
                    now_here.strftime("%Y-%m-%d"),
                    offset_str,
                ))
            except Exception:
                self.tree.insert("", "end", values=(location, tz_id, "—", "—", "—"))

    def _selected_row_data(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a row first.", parent=self)
            return None
        vals = self.tree.item(sel[0])["values"]
        return vals[0], vals[1]  # location, tz_id

    def _add(self):
        AddEditTimezoneDialog(self, self.prefs_manager, self.refresh_table)

    def _edit(self):
        data = self._selected_row_data()
        if data:
            AddEditTimezoneDialog(self, self.prefs_manager, self.refresh_table, edit_data=data)

    def _delete(self):
        data = self._selected_row_data()
        if not data:
            return
        if messagebox.askyesno("Confirm Delete",
                               f"Remove '{data[0]}' from the list?", parent=self):
            self.prefs_manager.delete_custom_timezone(data[0])
            self.refresh_table()


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class TimeZoneConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Time Zone Converter")
        self.hour_var = tk.StringVar(value="16")
        self.minute_var = tk.StringVar(value="0")
        self.local_timezone = get_localzone()
        self.prefs_manager = PreferencesManager()
        print("Loaded timezones:", self.prefs_manager.get_custom_timezones())
        self.calendar_popup = None

        self._apply_styles()
        self._build_ui()

    # ── Styles ────────────────────────────────────────────────────────────────

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        font=("Arial", 11),
                        rowheight=21,
                        background="white",
                        fieldbackground="white",
                        foreground="black")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        # ── Top bar: ⚙ Pref button flush right ──────────────────────────────
        top_bar = ttk.Frame(root)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 0))
        top_bar.grid_columnconfigure(0, weight=1)
        ttk.Button(top_bar, text="⚙  Pref", command=self._open_preferences) \
            .grid(row=0, column=1, sticky="e")

        select_bar = ttk.Frame(root)
        select_bar.grid(row=1, column=0, columnspan=7, sticky="ew", padx=10, pady=(8, 0)) 
        #select_bar.grid_columnconfigure(0, weight=1)


        # ── Date ─────────────────────────────────────────────────────────────
        ttk.Label(select_bar, text="Date").grid(row=1, column=0, padx=10, pady=2, sticky="w")
        today_str = datetime.now().date().strftime("%m/%d/%y")
        self.select_date_button = ttk.Button(select_bar, text=today_str, command=self._open_calendar)
        self.select_date_button.grid(row=1, column=1, padx=0, pady=2)

        # ── Hour ─────────────────────────────────────────────────────────────
        ttk.Label(select_bar, text="Hour").grid(row=1, column=2, padx=10, pady=10, sticky="w")
        self.hour_spinbox = ttk.Spinbox(select_bar, from_=0, to=23,
                                        textvariable=self.hour_var, wrap=True)
        self.hour_spinbox.grid(row=1, column=3, padx=3, pady=3, sticky="w")

        # ── Minute ───────────────────────────────────────────────────────────
        ttk.Label(select_bar, text="Minute").grid(row=1, column=4, padx=1, pady=1, sticky="w")
        self.minute_spinbox = ttk.Spinbox(select_bar, values=list(range(0, 60, 5)),
                                          textvariable=self.minute_var, wrap=True)
        self.minute_spinbox.grid(row=1, column=5, padx=3, pady=3, sticky="w")

        # ── Convert ───────────────────────────────────────────────────────────
        ttk.Button(select_bar, text="Convert", command=self._convert_time) \
            .grid(row=1, column=6, columnspan=6, padx=35, pady=10, sticky="e")

        # ── Results table ────────────────────────────────────────────────────
        result_frame = ttk.Frame(root)
        result_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.result_tree = ttk.Treeview(
            result_frame,
            columns=("ConTime", "ConDate", "Timezone"),
            style="Treeview",
            show="tree headings",
        )
        self.result_tree.heading("#0",       text="Location")
        self.result_tree.heading("ConTime",  text="Time")
        self.result_tree.heading("ConDate",  text="Target Date")
        self.result_tree.heading("Timezone", text="TZ ID")
        self.result_tree.pack(fill="both", expand=True)

        root.grid_rowconfigure(4, weight=1)
        root.grid_columnconfigure(0, weight=1)

    # ── Preferences ───────────────────────────────────────────────────────────

    def _open_preferences(self):
        PreferencesDialog(self.root, self.prefs_manager)

    # ── Calendar ──────────────────────────────────────────────────────────────

    def _open_calendar(self):
        if self.calendar_popup is None or not self.calendar_popup.winfo_exists():
            self.calendar_popup = tk.Toplevel(self.root)
            self.calendar_popup.title("Select Date")
            self.calendar = Calendar(self.calendar_popup, selectmode="day")
            self.calendar.pack(padx=10, pady=10)
            ttk.Button(self.calendar_popup, text="Select",
                       command=self._select_date).pack(pady=10)

    def _select_date(self):
        self.select_date_button.configure(text=self.calendar.get_date())
        self.calendar_popup.destroy()


    def convert_to_number(self, str_val, max):
        try:
            val = int(str_val)
            if 0 <= val <= max:
                return val
            
            if val < 0:
                return 0
            if val > max:
                return max
        except ValueError:
            pass
        return max
    # ── Conversion ────────────────────────────────────────────────────────────

    def _convert_time(self):
        selected_date = self.select_date_button.cget("text")
        selected_hour   = self.convert_to_number(self.hour_spinbox.get(), 23)
        self.hour_spinbox.set(f"{selected_hour:02d}")
        selected_minute = self.convert_to_number(self.minute_spinbox.get(), 59)
        self.minute_spinbox.set(f"{selected_minute:02d}")

        if not selected_date:
            base = datetime.now(self.local_timezone).replace(
                hour=selected_hour, minute=selected_minute, second=0, microsecond=0)
            input_dt = base.astimezone(pytz.utc)
        else:
            dt_str = f"{selected_date} {selected_hour:02d}:{selected_minute:02d}"
            naive  = datetime.strptime(dt_str, "%m/%d/%y %H:%M")
            input_dt = naive.astimezone(pytz.utc)

        # Clear previous results
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # Use timezones from preferences (re-read for freshness)
        for location, tz_id in self.prefs_manager.get_custom_timezones().items():
            try:
                tz = pytz.timezone(tz_id)
                converted = input_dt.astimezone(tz)
                self.result_tree.insert("", "end", text=location, values=(
                    converted.strftime("%H:%M"),
                    converted.strftime("%Y-%m-%d %Z"),
                    tz_id,
                ))
            except Exception:
                self.result_tree.insert("", "end", text=location,
                                        values=("Error", "Error", tz_id))


if __name__ == "__main__":
    root = tk.Tk()
    app = TimeZoneConverterApp(root)
    root.mainloop()