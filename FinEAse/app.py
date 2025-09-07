import sqlite3
import customtkinter as ctk
import tkinter.messagebox as messagebox
import hashlib
import datetime
import matplotlib.pyplot as plt
import openpyxl

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('expenses.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        budget REAL DEFAULT 1000
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        date TEXT,
        category TEXT,
        amount REAL,
        description TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        due_date TEXT,
        amount REAL,
        description TEXT,
        notified INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')
conn.commit()

# Global variable for logged-in user
logged_in_user = None

# Hashing function for secure password storage
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to register a new user
def register_user():
    username = reg_username_entry.get()
    password = reg_password_entry.get()
    hashed_password = hash_password(password)
    
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        messagebox.showinfo("Registration Successful", "You have registered successfully!")
        reg_window.destroy()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists. Please choose a different username.")

# Function to verify login
def login_user():
    global logged_in_user
    username = login_username_entry.get()
    password = login_password_entry.get()
    hashed_password = hash_password(password)
    
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    
    if user:
        logged_in_user = user[0]
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        login_window.destroy()
        open_main_window()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

# Function to add a new expense for the logged-in user
def add_expense(date, category, amount, description=""):
    if logged_in_user is None:
        messagebox.showerror("Error", "You must be logged in to add expenses.")
        return

    cursor.execute('''INSERT INTO expenses (user_id, date, category, amount, description) VALUES (?, ?, ?, ?, ?)''', 
                   (logged_in_user, date, category, amount, description))
    conn.commit()

# GUI function to add an expense
def add_expense_gui():
    try:
        date = date_entry.get()
        category = category_entry.get()
        amount = float(amount_entry.get())
        description = description_entry.get()
        add_expense(date, category, amount, description)
        messagebox.showinfo("Expense Tracker", "Expense added successfully!")
        clear_entries()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid amount.")

def clear_entries():
    date_entry.delete(0, ctk.END)
    category_entry.delete(0, ctk.END)
    amount_entry.delete(0, ctk.END)
    description_entry.delete(0, ctk.END)

# Function to check budget status
def check_budget():
    total_spent = get_total_spent()
    budget = get_user_budget()
    remaining_budget = budget - total_spent
    message = f"Total spent this month: ₹{total_spent}\nRemaining budget: ₹{remaining_budget}"
    if total_spent > budget:
        message += "\nWarning: You've exceeded your budget!"
    messagebox.showinfo("Budget Status", message)

# Function to get user-defined budget
def get_user_budget():
    cursor.execute("SELECT budget FROM users WHERE id = ?", (logged_in_user,))
    budget = cursor.fetchone()[0]
    return budget

# Function to set user-defined budget
def set_user_budget():
    try:
        new_budget = float(budget_entry.get())
        cursor.execute("UPDATE users SET budget = ? WHERE id = ?", (new_budget, logged_in_user))
        conn.commit()
        messagebox.showinfo("Budget Updated", f"Your budget has been updated to ₹{new_budget}.")
        budget_entry.delete(0, ctk.END)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid budget amount.")

# Function to get total spent by the user
def get_total_spent():
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (logged_in_user,))
    total = cursor.fetchone()[0]
    return total if total is not None else 0.0

# Function to get spending by category
def get_spending_by_category():
    cursor.execute('SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category', (logged_in_user,))
    categories = cursor.fetchall()
    if categories:
        category_info = "\n".join([f"{category}: ₹{total}" for category, total in categories])
        messagebox.showinfo("Spending by Category", category_info)
    else:
        messagebox.showinfo("Spending by Category", "No expenses recorded.")

# Function to visualize expenses
def visualize_expenses():
    cursor.execute('SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category', (logged_in_user,))
    data = cursor.fetchall()
    
    if not data:
        messagebox.showinfo("Visualization", "No data available for visualization.")
        return
    
    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]
    
    plt.figure(figsize=(10, 5))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
    plt.title("Spending by Category (INR)")
    plt.show()

# Function to view transaction history
def view_transaction_history():
    history_window = ctk.CTkToplevel(root)
    history_window.title("Transaction History")
    history_window.geometry("600x400")

    tree = ctk.CTkTabview(history_window, columns=("Date", "Category", "Amount", "Description"), show="headings")
    tree.heading("Date", text="Date")
    tree.heading("Category", text="Category")
    tree.heading("Amount", text="Amount (INR)")
    tree.heading("Description", text="Description")

    cursor.execute("SELECT date, category, amount, description FROM expenses WHERE user_id = ?", (logged_in_user,))
    for row in cursor.fetchall():
        tree.insert("", ctk.END, values=row)
    
    tree.pack(expand=True, fill='both')

# Function to check and display due alerts for the logged-in user
def check_due_alerts():
    today = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM alerts WHERE user_id = ? AND due_date = ? AND notified = 0", (logged_in_user, today))
    alerts = cursor.fetchall()

    if alerts:
        for alert in alerts:
            amount, description = alert[3], alert[4]
            messagebox.showinfo("Payment Alert", f"Reminder: You have a payment due today of ₹{amount}.\nDescription: {description}")
            cursor.execute("UPDATE alerts SET notified = 1 WHERE id = ?", (alert[0],))
        conn.commit()

# Function to add a payment alert
def add_payment_alert(due_date, amount, description=""):
    if logged_in_user is None:
        messagebox.showerror("Error", "You must be logged in to add payment alerts.")
        return

    cursor.execute('''INSERT INTO alerts (user_id, due_date, amount, description, notified) VALUES (?, ?, ?, ?, 0)''', 
                   (logged_in_user, due_date, amount, description))
    conn.commit()

# GUI function to add a payment alert with immediate check for testing
def add_alert_gui():
    try:
        due_date = alert_date_entry.get()
        amount = float(alert_amount_entry.get())
        description = alert_description_entry.get()
        add_payment_alert(due_date, amount, description)
        messagebox.showinfo("Payment Alert", "Alert added successfully!")
        # Immediate alert check for testing purposes
        check_due_alerts()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid amount.")
        # Function to export user expenses data to an Excel file
def export_data_to_excel():
    if logged_in_user is None:
        messagebox.showerror("Error", "You must be logged in to export data.")
        return
    
    # Create a new workbook and select the active sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Expenses"

    # Add headers to the sheet
    sheet.append(["Date", "Category", "Amount", "Description"])

    # Fetch the user's expenses from the database
    cursor.execute("SELECT date, category, amount, description FROM expenses WHERE user_id = ?", (logged_in_user,))
    expenses = cursor.fetchall()

    if not expenses:
        messagebox.showinfo("Export", "No expenses found to export.")
        return

    # Add data rows to the sheet
    for expense in expenses:
        sheet.append(expense)

    # Save the workbook to an Excel file
    try:
        file_path = f"expenses_{logged_in_user}.xlsx"
        workbook.save(file_path)
        messagebox.showinfo("Export Successful", f"Expenses data has been exported to {file_path}.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {str(e)}")

# Main GUI for logged-in user
def open_main_window():
    global root, date_entry, category_entry, amount_entry, description_entry, budget_entry, alert_date_entry, alert_amount_entry, alert_description_entry
    
    root = ctk.CTk()
    root.title("Expense Tracker")
    root.geometry("600x500")
    ctk.set_appearance_mode("System")  # or "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Customize color theme

    # Export data frame
    export_frame = ctk.CTkFrame(root)
    export_frame.pack(pady=10)
    ctk.CTkButton(export_frame, text="Export Expenses to Excel", command=export_data_to_excel).pack(pady=5)

    # Expense frame
    expense_frame = ctk.CTkFrame(root)
    expense_frame.pack(pady=10)
    ctk.CTkLabel(expense_frame, text="Add Expense", font=("Helvetica", 16)).grid(row=0, columnspan=2)

    ctk.CTkLabel(expense_frame, text="Date:").grid(row=1, column=0)
    date_entry = ctk.CTkEntry(expense_frame)
    date_entry.grid(row=1, column=1)

    ctk.CTkLabel(expense_frame, text="Category:").grid(row=2, column=0)
    category_entry = ctk.CTkEntry(expense_frame)
    category_entry.grid(row=2, column=1)

    ctk.CTkLabel(expense_frame, text="Amount (INR):").grid(row=3, column=0)
    amount_entry = ctk.CTkEntry(expense_frame)
    amount_entry.grid(row=3, column=1)

    ctk.CTkLabel(expense_frame, text="Description:").grid(row=4, column=0)
    description_entry = ctk.CTkEntry(expense_frame)
    description_entry.grid(row=4, column=1)

    ctk.CTkButton(expense_frame, text="Add Expense", command=add_expense_gui).grid(row=5, columnspan=2, pady=10)

    # Budget frame
    budget_frame = ctk.CTkFrame(root)
    budget_frame.pack(pady=10)
    ctk.CTkLabel(budget_frame, text="Set Budget", font=("Helvetica", 16)).pack()

    budget_entry = ctk.CTkEntry(budget_frame)
    budget_entry.pack(pady=5)

    ctk.CTkButton(budget_frame, text="Set Budget", command=set_user_budget).pack(pady=5)
    ctk.CTkButton(budget_frame, text="Check Budget", command=check_budget).pack(pady=5)

    # Alerts frame
    alert_frame = ctk.CTkFrame(root)
    alert_frame.pack(pady=10)
    ctk.CTkLabel(alert_frame, text="Add Payment Alert", font=("Helvetica", 16)).pack()

    alert_date_entry = ctk.CTkEntry(alert_frame)
    alert_date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
    alert_date_entry.pack(pady=5)

    alert_amount_entry = ctk.CTkEntry(alert_frame)
    alert_amount_entry.pack(pady=5)

    alert_description_entry = ctk.CTkEntry(alert_frame)
    alert_description_entry.pack(pady=5)

    ctk.CTkButton(alert_frame, text="Add Alert", command=add_alert_gui).pack(pady=5)

    # Visualization frame
    visualization_frame = ctk.CTkFrame(root)
    visualization_frame.pack(pady=10)
    ctk.CTkButton(visualization_frame, text="View Spending by Category", command=get_spending_by_category).pack(pady=5)
    ctk.CTkButton(visualization_frame, text="Visualize Expenses", command=visualize_expenses).pack(pady=5)

    # History frame
    history_frame = ctk.CTkFrame(root)
    history_frame.pack(pady=10)
    ctk.CTkButton(history_frame, text="View Transaction History", command=view_transaction_history).pack(pady=5)

    # Periodically check for due alerts
    root.after(86400000, check_due_alerts)  # Check every 24 hours (86400000 ms)

    root.mainloop()

# Main function to run the application
def open_login_window():
    global login_window, login_username_entry, login_password_entry, reg_window, reg_username_entry, reg_password_entry
    
    login_window = ctk.CTkToplevel()
    login_window.title("Login")
    login_window.geometry("300x200")

    ctk.CTkLabel(login_window, text="Username:").pack()
    login_username_entry = ctk.CTkEntry(login_window)
    login_username_entry.pack()

    ctk.CTkLabel(login_window, text="Password:").pack()
    login_password_entry = ctk.CTkEntry(login_window, show='*')
    login_password_entry.pack()

    ctk.CTkButton(login_window, text="Login", command=login_user).pack(pady=10)
    ctk.CTkButton(login_window, text="Register", command=open_registration_window).pack()

# GUI for registration
def open_registration_window():
    global reg_window, reg_username_entry, reg_password_entry
    
    reg_window = ctk.CTkToplevel()
    reg_window.title("Register")
    reg_window.geometry("300x200")

    ctk.CTkLabel(reg_window, text="Choose a Username:").pack()
    reg_username_entry = ctk.CTkEntry(reg_window)
    reg_username_entry.pack()

    ctk.CTkLabel(reg_window, text="Choose a Password:").pack()
    reg_password_entry = ctk.CTkEntry(reg_window, show='*')
    reg_password_entry.pack()

    ctk.CTkButton(reg_window, text="Register", command=register_user).pack()

# Main function to run the application
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("FinEase")
    root.geometry("300x150")

    ctk.CTkLabel(root, text="W E L C O M E", font=("Helvetica", 16)).pack(pady=20)
    ctk.CTkButton(root, text="Login", command=open_login_window).pack(pady=5)
    ctk.CTkButton(root, text="Register", command=open_registration_window).pack(pady=5)

    root.mainloop()

# Close the database connection on exit
conn.close()  
