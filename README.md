# Time Zone converter[^1]

A tkinter project to convert timezones, a day to day useful utility for people who need a application to see time across zones to set up meetings, classes etc.

## Features

- Convert time across multiple timezones
- Select date and time
- Add custom timezones with custom names
- Preferences saved in Windows user data (%APPDATA%)
- Automatic offset calculation from local timezone

## Setup
To set up the Time Zone Converter application, follow these steps:

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Install the required dependencies using pip:

```
pip install -r requirements.txt
```

### Create the EXE
run once on the machine or the venv `pip install pyinstaller` 
Navigate to the project directory and run:

```bash
python -m PyInstaller --hidden-import=babel.numbers --collect-all tkinter --onefile TimeZoneConverterApp.py --windowed
```

The executable will be created in the `dist\` folder as `TimeZoneConverterApp.exe`

#### Optional: Add Icon

To include a custom icon:

```bash
python -m PyInstaller --hidden-import=babel.numbers --collect-all tkinter --onefile --icon=icon.ico TimeZoneConverterApp.py
```

## Preferences

Timezone preferences are stored in:
```
%APPDATA%\TimeZoneConverter\preferences.json
```

On first run, default timezones are automatically created. You can add, edit, or delete timezones from the Preferences dialog (⚙ Pref button).

## Usage
1. Run the application by executing the `TimeZoneConverterApp.py` file.
2. Select the desired date and time using the provided controls.
3. Choose the target time zone from the available options.
4. Click the "Convert" button to see the converted time displayed in the results section.

## Contributing
Contributions to the Time Zone Converter application are welcome! If you have suggestions for improvements or new features, please feel free to submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

This project served as a prototype for full fledged android app https://github.com/agrsachin81/timezonecnverter_android



[^1]: Developed in a day with help of ChatGPT .
