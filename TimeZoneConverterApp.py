import tkinter as tk
from tkinter import ttk
from datetime import datetime
import pytz
from tzlocal import get_localzone
from tkcalendar import Calendar

#pyinstaller --hidden-import babel.numbers --onefile .\TimeZoneConverterApp.py


class TimeZoneConverterApp:
    def __init__(self, root):
        self.root = root
        self.hour_var = tk.StringVar(value="16")
        self.minute_var = tk.StringVar(value="0")
        self.root.title("Time Zone Converter")

        self.local_timezone = get_localzone()  # Automatically detect the local timezone

        self.date_label = ttk.Label(root, text="Select Date:")
        self.date_label.grid(row=0, column=0, padx=10, pady=10)

        today_date = datetime.now().date().strftime("%m/%d/%y")

        self.select_date_button = ttk.Button(root, text=today_date, command=self.open_calendar)
        self.select_date_button.grid(row=0, column=1, padx=10, pady=10)

        self.hour_label = ttk.Label(root, text="Select Hour:")
        self.hour_label.grid(row=1, column=0, padx=10, pady=10)
        self.hour_spinbox = ttk.Spinbox(root, from_=0, to=23, textvariable=self.hour_var, wrap=True)
        self.hour_spinbox.grid(row=1, column=1, padx=10, pady=10)

        self.minute_label = ttk.Label(root, text="Select Minute:")
        self.minute_label.grid(row=2, column=0, padx=10, pady=10)
        self.minute_spinbox = ttk.Spinbox(root, values=[i for i in range(0, 60, 5)], textvariable=self.minute_var,
                                          wrap=True)
        self.minute_spinbox.grid(row=2, column=1, padx=10, pady=10)

        self.convert_button = ttk.Button(root, text="Convert", command=self.convert_time)
        self.convert_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.result_frame = ttk.Frame(root)
        self.result_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        font=('Arial', 11),
                        rowheight=21,
                        background="white",
                        fieldbackground="white",
                        foreground="black")
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))

        self.result_tree = ttk.Treeview(self.result_frame, columns=("ConTime", "ConDate", "Timezone"), style="Treeview", show="tree headings")
        self.result_tree.heading("#0", text="Location")
        self.result_tree.heading("ConTime", text="Time")
        self.result_tree.heading("ConDate", text="Target Date")
        self.result_tree.heading("Timezone", text="TZ ID")
        self.result_tree.pack()

        # Configure grid resizing behavior
        root.grid_rowconfigure(4, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self.calendar_popup = None

    def open_calendar(self):
        if self.calendar_popup is None or not self.calendar_popup.winfo_exists():
            self.calendar_popup = tk.Toplevel(self.root)
            self.calendar_popup.title("Select Date")
            self.calendar = Calendar(self.calendar_popup, selectmode='day')
            self.calendar.pack(padx=10, pady=10)
            select_button = ttk.Button(self.calendar_popup, text="Select", command=self.select_date)
            select_button.pack(pady=10)

    def select_date(self):
        selected_date = self.calendar.get_date()
        self.select_date_button.configure(text=selected_date)
        self.calendar_popup.destroy()

    def convert_time(self):
        selected_date = self.select_date_button.cget("text")

        if not selected_date:
            today_date = datetime.now(self.local_timezone)
            selected_hour = int(self.hour_spinbox.get())
            selected_minute = int(self.minute_spinbox.get())
            input_datetime = today_date.replace(hour=selected_hour, minute=selected_minute, second=0, microsecond=0)
            # Convert input_datetime to UTC
            input_datetime = input_datetime.astimezone(pytz.utc)
        else:
            selected_hour = int(self.hour_spinbox.get())
            selected_minute = int(self.minute_spinbox.get())

            # Use the selected date and time in local timezone
            input_datetime_str = f"{selected_date} {selected_hour:02d}:{selected_minute:02d}"
            input_datetime = datetime.strptime(input_datetime_str, "%m/%d/%y %H:%M")
            # Convert input_datetime to UTC
            input_datetime = input_datetime.astimezone(pytz.utc)
            # self.local_timezone.localize(input_datetime).astimezone(pytz.utc))

        # Clear previous results
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # List of timezones to display
        output_timezones = ['Asia/Dubai', 'Asia/Riyadh', 'America/New_York', 'Europe/Amsterdam', 'Europe/London',
                            'Pacific/Fiji', 'Pacific/Port_Moresby', 'America/Chicago']

        location_timezone_mapping = {
            "New York": "America/New_York",
            "Texas": "America/Chicago",
            "Netherlands": "Europe/Amsterdam",
            "UK": "Europe/London",
            "Dubai": "Asia/Dubai",
            "Saudi Arabia": "Asia/Riyadh",
            "Fiji": "Pacific/Fiji",
            "PNG": "Pacific/Port_Moresby"
        }
        # Add labels for each timezone in the result frame
        for i, (location, timezone_id) in enumerate(location_timezone_mapping.items(), start=0):
            tz = pytz.timezone(timezone_id)
            converted_dt = input_datetime.astimezone(tz)
            # label_text = f"{timezone}: {converted_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            # label = ttk.Label(self.result_frame, text=label_text)
            # label.grid(row=i, column=0, sticky="w")

            self.result_tree.insert("", "end", text= location,
                                    values=(converted_dt.strftime('%H:%M'), converted_dt.strftime('%Y-%m-%d %Z'), timezone_id))


if __name__ == "__main__":
    root = tk.Tk()
    app = TimeZoneConverterApp(root)
    root.mainloop()
