import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('hospital.db')

# Create a cursor object
cursor = conn.cursor()

# Create the patients table
cursor.execute('''
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    contact TEXT NOT NULL,
    address TEXT NOT NULL,
    symptoms TEXT,
    diagnosis TEXT,
    lab_results TEXT,
    prescribed_medicine TEXT,
    bill_amount REAL
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()
