from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def get_db():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- Dashboard ----------------
@app.route('/')
def dashboard():
    db = get_db()
    today_sql = datetime.now().strftime('%Y-%m-%d')
    today_display = datetime.now().strftime('%A, %B %d, %Y')

    stats = {
        'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
        'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
        'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
        'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
        'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today_sql,)).fetchone()[0],
        'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
        'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
        'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
        'efficiency': 0  # You can calculate this based on completed vs total appointments
    }

    return render_template('dashboard.html', stats=stats, current_date=today_display)

# ---------------- Patient Registration ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        db = get_db()
        db.execute("""
            INSERT INTO patients (
                medical_record_number, first_name, last_name, age, gender, contact, address,
                is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            data['medical_record_number'], data['first_name'], data['last_name'],
            data['age'], data['gender'], data['contact'], data['address']
        ))
        db.commit()
        flash('Patient registered successfully!')
        return redirect(url_for('register'))
    return render_template('register.html')

# ---------------- Doctor Interface ----------------
@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        symptoms = request.form['symptoms']
        diagnosis = request.form['diagnosis']
        db = get_db()
        db.execute("UPDATE patients SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (symptoms, diagnosis, patient_id))
        db.commit()
        flash('Diagnosis saved successfully!')
        return redirect(url_for('doctor'))
    return render_template('doctor.html')

# ---------------- Lab Results ----------------
@app.route('/lab', methods=['GET', 'POST'])
def lab():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        lab_results = request.form['lab_results']
        db = get_db()
        db.execute("UPDATE patients SET lab_results = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (lab_results, patient_id))
        db.commit()
        flash('Lab results saved successfully!')
        return redirect(url_for('lab'))
    return render_template('lab.html')

# ---------------- Pharmacy ----------------
@app.route('/pharmacist', methods=['GET', 'POST'])
def pharmacist():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        prescribed_medicine = request.form['prescribed_medicine']
        db = get_db()
        db.execute("UPDATE patients SET prescribed_medicine = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (prescribed_medicine, patient_id))
        db.commit()
        flash('Prescribed medicine saved successfully!')
        return redirect(url_for('pharmacist'))
    return render_template('pharmacist.html')

# ---------------- Billing ----------------
@app.route('/cashier', methods=['GET', 'POST'])
def cashier():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        bill_amount = request.form['bill_amount']
        db = get_db()
        db.execute("UPDATE patients SET bill_amount = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (bill_amount, patient_id))
        db.commit()
        flash('Bill paid successfully!')
        return redirect(url_for('cashier'))
    return render_template('cashier.html')

# ---------------- Patient Detail ----------------
@app.route('/patient/<int:id>')
def patient_detail(id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
    return render_template('patient_detail.html', patient=patient)

# ---------------- Patient List ----------------
@app.route('/patients')
def patients():
    db = get_db()
    patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
    return render_template('patients.html', patients=patients)

if __name__ == '__main__':
    app.run(debug=True)




# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3
# from datetime import datetime

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'

# def get_db():
#     conn = sqlite3.connect('hospital.db')
#     conn.row_factory = sqlite3.Row
#     return conn

# # ---------------- Dashboard ----------------
# @app.route('/')
# def dashboard():
#     db = get_db()
#     today = datetime.now().strftime('%Y-%m-%d')
#     stats = {
#         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
#         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today,)).fetchone()[0],
#         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
#         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today,)).fetchone()[0]
#     }
#     return render_template('dashboard.html', stats=stats)

# # ---------------- Patient Registration ----------------
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         data = request.form
#         db = get_db()
#         db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             data['medical_record_number'], data['first_name'], data['last_name'],
#             data['age'], data['gender'], data['contact'], data['address']
#         ))
#         db.commit()
#         flash('Patient registered successfully!')
#         return redirect(url_for('register'))
#     return render_template('register.html')

# # ---------------- Doctor Interface ----------------
# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
#         db = get_db()
#         db.execute("UPDATE patients SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
#                    (symptoms, diagnosis, patient_id))
#         db.commit()
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('doctor'))
#     return render_template('doctor.html')

# # ---------------- Lab Results ----------------
# @app.route('/lab', methods=['GET', 'POST'])
# def lab():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         lab_results = request.form['lab_results']
#         db = get_db()
#         db.execute("UPDATE patients SET lab_results = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
#                    (lab_results, patient_id))
#         db.commit()
#         flash('Lab results saved successfully!')
#         return redirect(url_for('lab'))
#     return render_template('lab.html')

# # ---------------- Pharmacy ----------------
# @app.route('/pharmacist', methods=['GET', 'POST'])
# def pharmacist():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         prescribed_medicine = request.form['prescribed_medicine']
#         db = get_db()
#         db.execute("UPDATE patients SET prescribed_medicine = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
#                    (prescribed_medicine, patient_id))
#         db.commit()
#         flash('Prescribed medicine saved successfully!')
#         return redirect(url_for('pharmacist'))
#     return render_template('pharmacist.html')

# # ---------------- Billing ----------------
# @app.route('/cashier', methods=['GET', 'POST'])
# def cashier():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         bill_amount = request.form['bill_amount']
#         db = get_db()
#         db.execute("UPDATE patients SET bill_amount = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
#                    (bill_amount, patient_id))
#         db.commit()
#         flash('Bill paid successfully!')
#         return redirect(url_for('cashier'))
#     return render_template('cashier.html')

# # ---------------- Patient Detail ----------------
# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
#     return render_template('patient_detail.html', patient=patient)

# # ---------------- Patient List ----------------
# @app.route('/patients')
# def patients():
#     db = get_db()
#     patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
#     return render_template('patients.html', patients=patients)

# if __name__ == '__main__':
#     app.run(debug=True)












# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'

# def connect_db():
#     return sqlite3.connect('hospital.db')

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form['name']
#         age = request.form['age']
#         gender = request.form['gender']
#         contact = request.form['contact']
#         address = request.form['address']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
#                        (name, age, gender, contact, address))
#         conn.commit()
#         conn.close()
        
#         flash('Patient registered successfully!')
#         return redirect(url_for('home'))
#     return render_template('register.html')

# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
#                        (symptoms, diagnosis, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('doctor.html')

# @app.route('/lab', methods=['GET', 'POST'])
# def lab():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         lab_results = request.form['lab_results']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
#                        (lab_results, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Lab results saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('lab.html')

# @app.route('/pharmacist', methods=['GET', 'POST'])
# def pharmacist():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         prescribed_medicine = request.form['prescribed_medicine']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
#                        (prescribed_medicine, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Prescribed medicine saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('pharmacist.html')

# @app.route('/cashier', methods=['GET', 'POST'])
# def cashier():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         bill_amount = request.form['bill_amount']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
#                        (bill_amount, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Bill paid successfully!')
#         return redirect(url_for('home'))
#     return render_template('cashier.html')

# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()
#     conn.close()
#     return render_template('patient_detail.html', patient=patient)

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)


# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'

# def connect_db():
#     return sqlite3.connect('hospital.db')

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form['name']
#         age = request.form['age']
#         gender = request.form['gender']
#         contact = request.form['contact']
#         address = request.form['address']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
#                        (name, age, gender, contact, address))
#         conn.commit()
#         conn.close()
        
#         flash('Patient registered successfully!')
#         return redirect(url_for('home'))
#     return render_template('register.html')

# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
#                        (symptoms, diagnosis, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('doctor.html')

# @app.route('/lab', methods=['GET', 'POST'])
# def lab():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         lab_results = request.form['lab_results']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
#                        (lab_results, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Lab results saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('lab.html')

# @app.route('/pharmacist', methods=['GET', 'POST'])
# def pharmacist():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         prescribed_medicine = request.form['prescribed_medicine']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
#                        (prescribed_medicine, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Prescribed medicine saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('pharmacist.html')

# @app.route('/cashier', methods=['GET', 'POST'])
# def cashier():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         bill_amount = request.form['bill_amount']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
#                        (bill_amount, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Bill paid successfully!')
#         return redirect(url_for('home'))
#     return render_template('cashier.html')

# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()
#     conn.close()
#     return render_template('patient_detail.html', patient=patient)

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)





# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'

# def connect_db():
#     return sqlite3.connect('hospital.db')

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form['name']
#         age = request.form['age']
#         gender = request.form['gender']
#         contact = request.form['contact']
#         address = request.form['address']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
#                        (name, age, gender, contact, address))
#         conn.commit()
#         conn.close()
        
#         flash('Patient registered successfully!')
#         return redirect(url_for('home'))
#     return render_template('register.html')

# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
#                        (symptoms, diagnosis, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('doctor.html')

# @app.route('/lab', methods=['GET', 'POST'])
# def lab():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         lab_results = request.form['lab_results']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
#                        (lab_results, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Lab results saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('lab.html')

# @app.route('/pharmacist', methods=['GET', 'POST'])
# def pharmacist():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         prescribed_medicine = request.form['prescribed_medicine']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
#                        (prescribed_medicine, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Prescribed medicine saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('pharmacist.html')

# @app.route('/cashier', methods=['GET', 'POST'])
# def cashier():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         bill_amount = request.form['bill_amount']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
#                        (bill_amount, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Bill paid successfully!')
#         return redirect(url_for('home'))
#     return render_template('cashier.html')

# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()
#     conn.close()
#     return render_template('patient_detail.html', patient=patient)

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)






# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'  # Necessary for flash messages

# def connect_db():
#     return sqlite3.connect('hospital.db')

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form['name']
#         age = request.form['age']
#         gender = request.form['gender']
#         contact = request.form['contact']
#         address = request.form['address']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
#                        (name, age, gender, contact, address))
#         conn.commit()
#         conn.close()
        
#         flash('Patient registered successfully!')
#         return redirect(url_for('home'))
#     return render_template('register.html')

# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
#                        (symptoms, diagnosis, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('doctor.html')

# @app.route('/lab', methods=['GET', 'POST'])
# def lab():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         lab_results = request.form['lab_results']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
#                        (lab_results, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Lab results saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('lab.html')

# @app.route('/pharmacist', methods=['GET', 'POST'])
# def pharmacist():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         prescribed_medicine = request.form['prescribed_medicine']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
#                        (prescribed_medicine, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Prescribed medicine saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('pharmacist.html')

# @app.route('/cashier', methods=['GET', 'POST'])
# def cashier():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         bill_amount = request.form['bill_amount']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
#                        (bill_amount, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Bill paid successfully!')
#         return redirect(url_for('home'))
#     return render_template('cashier.html')

# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()
#     conn.close()
#     return render_template('patient_detail.html', patient=patient)

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)









# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'  # Necessary for flash messages

# def connect_db():
#     return sqlite3.connect('hospital.db')

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form['name']
#         age = request.form['age']
#         gender = request.form['gender']
#         contact = request.form['contact']
#         address = request.form['address']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
#                        (name, age, gender, contact, address))
#         conn.commit()
#         conn.close()
        
#         flash('Patient registered successfully!')
#         return redirect(url_for('home'))
#     return render_template('register.html')

# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
#                        (symptoms, diagnosis, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('doctor.html')

# @app.route('/lab', methods=['GET', 'POST'])
# def lab():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         lab_results = request.form['lab_results']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
#                        (lab_results, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Lab results saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('lab.html')

# @app.route('/pharmacist', methods=['GET', 'POST'])
# def pharmacist():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         prescribed_medicine = request.form['prescribed_medicine']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
#                        (prescribed_medicine, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Prescribed medicine saved successfully!')
#         return redirect(url_for('home'))
#     return render_template('pharmacist.html')

# @app.route('/cashier', methods=['GET', 'POST'])
# def cashier():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         bill_amount = request.form['bill_amount']
        
#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
#                        (bill_amount, patient_id))
#         conn.commit()
#         conn.close()
        
#         flash('Bill paid successfully!')
#         return redirect(url_for('home'))
#     return render_template('cashier.html')

# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()
#     conn.close()
#     return render_template('patient_detail.html', patient=patient)


# if __name__ == '__main__':
#     app.run(debug=True, port=5001)

# if __name__ == '__main__':
#     app.run(debug=True)




# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'  # For flash messages

# # Database connection
# def connect_db():
#     return sqlite3.connect('hospital.db')

# # Create tables (do this once to set up your database)
# def init_db():
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS patients (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT,
#             age INTEGER,
#             gender TEXT,
#             contact TEXT,
#             address TEXT,
#             symptoms TEXT,
#             diagnosis TEXT,
#             lab_results TEXT,
#             prescribed_medicine TEXT,
#             bill_amount REAL
#         )
#     ''')
#     conn.commit()
#     conn.close()

# # Home Route (Modified to pass patients)
# @app.route('/')
# @app.route('/')
# def home():
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients')
#     patients = cursor.fetchall()
#     conn.close()
#     return render_template('index.html', patients=patients)

# # def home():
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT id, name FROM patients')  # Fetch patient IDs and names
# #     patients = cursor.fetchall()
# #     conn.close()
# #     return render_template('index.html', patients=patients)

# # Reception: Register a patient
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form['name']
#         age = request.form['age']
#         gender = request.form['gender']
#         contact = request.form['contact']
#         address = request.form['address']

#         conn = connect_db()
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)', 
#                        (name, age, gender, contact, address))
#         conn.commit()
#         conn.close()

#         flash('Patient registered successfully!')
#         return redirect(url_for('home'))
#     return render_template('register.html')



# # Doctor: View and update patient details
# @app.route('/doctor/<int:id>', methods=['GET', 'POST'])
# def doctor(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()

#     if request.method == 'POST':
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
        
#         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?', 
#                        (symptoms, diagnosis, id))
#         conn.commit()
#         conn.close()

#         flash('Patient diagnosis updated!')
#         return redirect(url_for('doctor', id=id))

#     conn.close()
#     return render_template('doctor.html', patient=patient)

# # @app.route('/doctor/<int:id>', methods=['GET', 'POST'])
# # def doctor(id):
# #     # conn = connect_db()
# #     # cursor = conn.cursor()
# #     # cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# #     # patient = cursor.fetchone()


# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients')
# #     patients = cursor.fetchall()
# #     conn.close()

# #     if request.method == 'POST':
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
        
# #         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?', 
# #                        (symptoms, diagnosis, id))
# #         conn.commit()
# #         conn.close()

# #         flash('Patient diagnosis updated!')
# #         return redirect(url_for('doctor', id=id))

# #     conn.close()
# #     return render_template('doctor.html', patient=patient)

# # Lab: Enter lab results

# # @app.route('/lab/<int:id>', methods=['GET'])
# # def lab(id):
# #     # Example logic to handle the lab request
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM lab_tests WHERE patient_id = ?', (id,))
# #     lab_test = cursor.fetchone()
# #     conn.close()
# #     return render_template('lab.html', lab_test=lab_test)

# @app.route('/lab/<int:id>', methods=['GET', 'POST'])
# def lab(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()

#     if request.method == 'POST':
#         lab_results = request.form['lab_results']
#         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?', (lab_results, id))
#         conn.commit()
#         conn.close()

#         flash('Lab results updated!')
#         return redirect(url_for('doctor', id=id))

#     conn.close()
#     return render_template('lab.html', patient=patient)

# # Pharmacist: Dispense medicines
# @app.route('/pharmacist/<int:id>', methods=['GET', 'POST'])
# def pharmacist(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()

#     if request.method == 'POST':
#         prescribed_medicine = request.form['prescribed_medicine']
#         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?', 
#                        (prescribed_medicine, id))
#         conn.commit()
#         conn.close()

#         flash('Medicine prescribed!')
#         return redirect(url_for('doctor', id=id))

#     conn.close()
#     return render_template('pharmacist.html', patient=patient)

# # Cashier: Handle billing
# @app.route('/cashier/<int:id>', methods=['GET', 'POST'])
# def cashier(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()

#     if request.method == 'POST':
#         bill_amount = request.form['bill_amount']
#         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?', (bill_amount, id))
#         conn.commit()
#         conn.close()

#         flash('Bill payment recorded!')
#         return redirect(url_for('home'))

#     conn.close()
#     return render_template('cashier.html', patient=patient)

# # Display patient details
# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     conn = connect_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
#     patient = cursor.fetchone()
#     conn.close()
#     return render_template('patient_detail.html', patient=patient)

# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)






# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'  # For flash messages

# # # Database connection
# # def connect_db():
# #     return sqlite3.connect('hospital.db')

# # # Create tables (do this once to set up your database)
# # def init_db():
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS patients (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             name TEXT,
# #             age INTEGER,
# #             gender TEXT,
# #             contact TEXT,
# #             address TEXT,
# #             symptoms TEXT,
# #             diagnosis TEXT,
# #             lab_results TEXT,
# #             prescribed_medicine TEXT,
# #             bill_amount REAL
# #         )
# #     ''')
# #     conn.commit()
# #     conn.close()

# # # Home Route
# # @app.route('/')
# # def home():
# #     return render_template('index.html')

# # # Reception: Register a patient
# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         name = request.form['name']
# #         age = request.form['age']
# #         gender = request.form['gender']
# #         contact = request.form['contact']
# #         address = request.form['address']

# #         conn = connect_db()
# #         cursor = conn.cursor()
# #         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)', 
# #                        (name, age, gender, contact, address))
# #         conn.commit()
# #         conn.close()

# #         flash('Patient registered successfully!')
# #         return redirect(url_for('home'))
# #     return render_template('register.html')

# # # Doctor: View and update patient details
# # @app.route('/doctor/<int:id>', methods=['GET', 'POST'])
# # def doctor(id):
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# #     patient = cursor.fetchone()

# #     if request.method == 'POST':
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
        
# #         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?', 
# #                        (symptoms, diagnosis, id))
# #         conn.commit()
# #         conn.close()

# #         flash('Patient diagnosis updated!')
# #         return redirect(url_for('doctor', id=id))

# #     conn.close()
# #     return render_template('doctor.html', patient=patient)

# # # Lab: Enter lab results
# # @app.route('/lab/<int:id>', methods=['GET', 'POST'])
# # def lab(id):
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# #     patient = cursor.fetchone()

# #     if request.method == 'POST':
# #         lab_results = request.form['lab_results']
# #         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?', (lab_results, id))
# #         conn.commit()
# #         conn.close()

# #         flash('Lab results updated!')
# #         return redirect(url_for('doctor', id=id))

# #     conn.close()
# #     return render_template('lab.html', patient=patient)

# # # Pharmacist: Dispense medicines
# # @app.route('/pharmacist/<int:id>', methods=['GET', 'POST'])
# # def pharmacist(id):
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# #     patient = cursor.fetchone()

# #     if request.method == 'POST':
# #         prescribed_medicine = request.form['prescribed_medicine']
# #         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?', 
# #                        (prescribed_medicine, id))
# #         conn.commit()
# #         conn.close()

# #         flash('Medicine prescribed!')
# #         return redirect(url_for('doctor', id=id))

# #     conn.close()
# #     return render_template('pharmacist.html', patient=patient)

# # # Cashier: Handle billing
# # @app.route('/cashier/<int:id>', methods=['GET', 'POST'])
# # def cashier(id):
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# #     patient = cursor.fetchone()

# #     if request.method == 'POST':
# #         bill_amount = request.form['bill_amount']
# #         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?', (bill_amount, id))
# #         conn.commit()
# #         conn.close()

# #         flash('Bill payment recorded!')
# #         return redirect(url_for('home'))

# #     conn.close()
# #     return render_template('cashier.html', patient=patient)

# # # Display patient details
# # @app.route('/patient/<int:id>')
# # def patient_detail(id):
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# #     patient = cursor.fetchone()
# #     conn.close()
# #     return render_template('patient_detail.html', patient=patient)

# # if __name__ == '__main__':
# #     init_db()
# #     app.run(debug=True)







# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'  # Necessary for flash messages

# # def connect_db():
# #     return sqlite3.connect('hospital.db')

# # @app.route('/')
# # def home():
# #     return render_template('index.html')

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         name = request.form['name']
# #         age = request.form['age']
# #         gender = request.form['gender']
# #         contact = request.form['contact']
# #         address = request.form['address']
        
# #         conn = connect_db()
# #         cursor = conn.cursor()
# #         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
# #                        (name, age, gender, contact, address))
# #         conn.commit()
# #         conn.close()
        
# #         flash('Patient registered successfully!')
# #         return redirect(url_for('home'))
# #     return render_template('register.html')

# # @app.route('/doctor', methods=['GET', 'POST'])
# # def doctor():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
        
# #         conn = connect_db()
# #         cursor = conn.cursor()
# #         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
# #                        (symptoms, diagnosis, patient_id))
# #         conn.commit()
# #         conn.close()
        
# #         flash('Diagnosis saved successfully!')
# #         return redirect(url_for('home'))
# #     return render_template('doctor.html')

# # @app.route('/lab', methods=['GET', 'POST'])
# # def lab():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         lab_results = request.form['lab_results']
        
# #         conn = connect_db()
# #         cursor = conn.cursor()
# #         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
# #                        (lab_results, patient_id))
# #         conn.commit()
# #         conn.close()
        
# #         flash('Lab results saved successfully!')
# #         return redirect(url_for('home'))
# #     return render_template('lab.html')

# # @app.route('/pharmacist', methods=['GET', 'POST'])
# # def pharmacist():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         prescribed_medicine = request.form['prescribed_medicine']
        
# #         conn = connect_db()
# #         cursor = conn.cursor()
# #         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
# #                        (prescribed_medicine, patient_id))
# #         conn.commit()
# #         conn.close()
        
# #         flash('Prescribed medicine saved successfully!')
# #         return redirect(url_for('home'))
# #     return render_template('pharmacist.html')

# # @app.route('/cashier', methods=['GET', 'POST'])
# # def cashier():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         bill_amount = request.form['bill_amount']
        
# #         conn = connect_db()
# #         cursor = conn.cursor()
# #         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
# #                        (bill_amount, patient_id))
# #         conn.commit()
# #         conn.close()
        
# #         flash('Bill paid successfully!')
# #         return redirect(url_for('home'))
# #     return render_template('cashier.html')

# # @app.route('/patient/<int:id>')
# # def patient_detail(id):
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# #     patient = cursor.fetchone()
# #     conn.close()
# #     return render_template('patient_detail.html', patient=patient)

# # if __name__ == '__main__':
# #     app.run(debug=True)






# # # app.py
# # from app import create_app

# # # Create the app using the factory function
# # app = create_app()

# # if __name__ == '__main__':
# #     app.run(debug=True)




# # from flask import Flask
# # from app.routes import bp as main_bp

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

# # # Register the blueprint
# # app.register_blueprint(main_bp, url_prefix='/')

# # if __name__ == '__main__':
# #     app.run(debug=True)





# # from flask import Flask
# # from app.routes import bp as main_bp

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

# # # Register blueprint
# # app.register_blueprint(main_bp)

# # if __name__ == '__main__':
# #     app.run(debug=True)



# # from app import create_app

# # app = create_app()

# # if __name__ == '__main__':
# #     app.run(debug=True)
