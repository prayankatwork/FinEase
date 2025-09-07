# FinEAse

## Description

FinEAse is a desktop application built with CustomTkinter for managing personal finances. It allows users to register, log in, and track their expenses with a user-friendly graphical interface. The application stores data locally using SQLite and provides features for budgeting, expense visualization, alerts for due payments, and exporting expense data to Excel.

## Features

- User registration and login with secure password hashing.
- Add, view, and categorize expenses.
- Set and check monthly budgets.
- Visualize spending by category using pie charts.
- View transaction history in a tabular format.
- Add payment alerts with notifications.
- Export expense data to Excel files.
- Data persistence using SQLite database.

## Installation

1. Ensure Python is installed on your system.
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python app.py
   ```

## Usage

- Launch the app and register a new user or log in with existing credentials.
- Use the GUI to add expenses, set budgets, view reports, and manage alerts.
- Export your expense data to Excel for further analysis.

## Dependencies

- customtkinter: Modern Tkinter UI framework.
- matplotlib: For plotting expense visualizations.
- openpyxl: For exporting data to Excel.
- sqlite3: Built-in Python library for database management.

## Notes

- The application stores data in a local SQLite database file named `expenses.db`.
- Alerts notify users of due payments on the current date.
- The UI adapts to system appearance mode (light/dark).
