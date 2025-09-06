# import sqlite3

# def init_db():
#     # Connect to the SQLite database
#     conn = sqlite3.connect('hospital.db')

#     # Create a cursor object
#     cursor = conn.cursor()

#     # Create the patients table
#     cursor.execute('''
#     CREATE TABLE IF NOT EXISTS patients (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name TEXT NOT NULL,
#         age INTEGER NOT NULL,
#         gender TEXT NOT NULL,
#         contact TEXT NOT NULL,
#         address TEXT NOT NULL,
#         symptoms TEXT,
#         diagnosis TEXT,
#         lab_results TEXT,
#         prescribed_medicine TEXT,
#         bill_amount REAL
#     )
#     ''')

#     # Commit the changes and close the connection
#     conn.commit()
#     conn.close()

# if __name__ == "__main__":
#     init_db()

import sqlite3

def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()






# import sqlite3

# # Connect to the SQLite database
# conn = sqlite3.connect('hospital.db')

# # Create a cursor object
# cursor = conn.cursor()

# # Create the patients table
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS patients (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     age INTEGER NOT NULL,
#     gender TEXT NOT NULL,
#     contact TEXT NOT NULL,
#     address TEXT NOT NULL,
#     symptoms TEXT,
#     diagnosis TEXT,
#     lab_results TEXT,
#     prescribed_medicine TEXT,
#     bill_amount REAL
# )
# ''')

# # Commit the changes and close the connection
# conn.commit()






# import sqlite3

# # Connect to the SQLite database
# conn = sqlite3.connect('hospital.db')

# # Create a cursor object
# cursor = conn.cursor()

# # Create the patients table
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS patients (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     age INTEGER NOT NULL,
#     gender TEXT NOT NULL,
#     contact TEXT NOT NULL,
#     address TEXT NOT NULL,
#     symptoms TEXT,
#     diagnosis TEXT,
#     lab_results TEXT,
#     prescribed_medicine TEXT,
#     bill_amount REAL
# )
# ''')

# # Commit the changes and close the connection
# conn.commit()
# conn.close()




# import sqlite3

# conn = sqlite3.connect('hospital.db')
# cursor = conn.cursor()

# # Create tables
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS patients (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     age INTEGER,
#     gender TEXT,
#     address TEXT,
#     phone TEXT
# )
# ''')

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS doctors (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     specialization TEXT
# )
# ''')

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS reports (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     patient_id INTEGER,
#     doctor_id INTEGER,
#     symptoms TEXT,
#     diagnosis TEXT,
#     FOREIGN KEY(patient_id) REFERENCES patients(id),
#     FOREIGN KEY(doctor_id) REFERENCES doctors(id)
# )
# ''')

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS lab_tests (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     report_id INTEGER,
#     test_results TEXT,
#     FOREIGN KEY(report_id) REFERENCES reports(id)
# )
# ''')

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS prescriptions (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     report_id INTEGER,
#     medication TEXT,
#     dosage TEXT,
#     FOREIGN KEY(report_id) REFERENCES reports(id)
# )
# ''')

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS billing (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     patient_id INTEGER,
#     amount REAL,
#     paid INTEGER,
#     FOREIGN KEY(patient_id) REFERENCES patients(id)
# )
# ''')

# conn.commit()
# conn.close()



# import sqlite3

# # Connect to the SQLite database
# conn = sqlite3.connect('hospital.db')

# # Create a cursor object
# cursor = conn.cursor()

# # Create the patients table
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS patients (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     age INTEGER NOT NULL,
#     gender TEXT NOT NULL,
#     contact TEXT NOT NULL,
#     address TEXT NOT NULL,
#     symptoms TEXT,
#     diagnosis TEXT,
#     lab_results TEXT,
#     prescribed_medicine TEXT,
#     bill_amount REAL
# )
# ''')

# # Commit the changes and close the connection
# conn.commit()
# conn.close()
