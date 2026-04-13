import os
import json

class PreferencesManager:

    default_timezone_mapping = {
        "New York": "America/New_York",
        "Texas": "America/Chicago",
        "Netherlands": "Europe/Amsterdam",
        "UK": "Europe/London",
        "Dubai": "Asia/Dubai",
        "Saudi Arabia": "Asia/Riyadh",
        "Fiji": "Pacific/Fiji",
        "PNG": "Pacific/Port_Moresby",
    }
    
    def __init__(self):
        self.preferences_file = os.path.join(os.environ.get('APPDATA', ''), 'TZC_v2', 'preferences.json')
        self.custom_timezones = self.load_preferences()

    def load_preferences(self):
        if os.path.exists(self.preferences_file):
            with open(self.preferences_file, 'r') as f:
                return json.load(f)
        self.custom_timezones = self.default_timezone_mapping.copy()
        self.save_preferences()
        return self.custom_timezones

    def save_preferences(self):
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
        with open(self.preferences_file, 'w') as f:
            json.dump(self.custom_timezones, f, indent=4)

    def add_custom_timezone(self, name, timezone):
        self.custom_timezones[name] =  timezone
        self.save_preferences()

    def get_custom_timezones(self):
        return self.custom_timezones.copy()

    def delete_custom_timezone(self, name):
        if name in self.custom_timezones:
            del self.custom_timezones[name]
            self.save_preferences()