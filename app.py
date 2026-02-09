from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import africastalking
from flask import make_response
from weasyprint import HTML
from flask_login import LoginManager
from flask_login import login_required
from werkzeug.security import check_password_hash
from flask_login import LoginManager


import africastalking

# # Sandbox credentials
# username = "sandbox"
# api_key = "YOUR_SANDBOX_API_KEY"

# # Manually initialize only SMS service
# sms = africastalking.SMS
# sms.username = username
# sms.api_key = api_key









app = Flask(__name__)  # Your existing app setup

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # This should match your login route name




# Initialize Africa's Talking SDK
import africastalking

# username = "sandbox"  # or your live username
# api_key = "your_actual_api_key"

# africastalking.initialize(username, api_key)
# sms = africastalking.SMS
# sms.send("New prescription for Patient XYZ", ["+254711732324"])

# africastalking.initialize(username="your_username", api_key="your_api_key")
# sms = africastalking.SMS
# sms.send("New prescription for Patient XYZ", ["+254711732324"])

login_manager.login_view = 'login'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            login_user(User(user))  # wrap in your User class
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))  # or wherever you want to land
        else:
            flash('Invalid credentials')

    return render_template('login.html')


# @login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(user) if user else None


login_manager.login_view = 'user_login'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('login'))


app = Flask(__name__)
app.secret_key = 'supersecretkey'

# ---------------- Database Connection ----------------
def get_db():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'  # or whatever your login route is


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(user) if user else None  # Wrap in your User class


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

class User:
    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.role = row['role']

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


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
        'efficiency': 0
    }

    queue = db.execute("""
    SELECT a.id, p.first_name || ' ' || p.last_name AS patient_name, a.status
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    WHERE DATE(a.appointment_date) = ? AND a.status IN ('scheduled', 'confirmed')
    ORDER BY a.appointment_date ASC
""", (today_sql,)).fetchall()


    if stats['today_appointments'] > 0:
        stats['efficiency'] = round((stats['completed_appointments_today'] / stats['today_appointments']) * 100, 2)

    appointments = db.execute("""
        SELECT a.*, 
               p.first_name || ' ' || p.last_name AS patient_name,
               d.first_name || ' ' || d.last_name AS doctor_name,
               strftime('%H:%M', a.appointment_date) AS time
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE DATE(a.appointment_date) = ?
        ORDER BY a.appointment_date ASC
    """, (today_sql,)).fetchall()

    return render_template('dashboard.html', stats=stats, appointments=appointments, current_date=today_display)


@app.route('/dashboard')
def dashboard_view():
    stats = {
        'total_patients': 120,
        'total_doctors': 15,
        'today_appointments': 8,
        'pending_appointments': 3,
        'completed_appointments_today': 5,
        'efficiency': 83,
        'available_beds': 12,
        'in_labor': 2
    }

    stats_grid = [
        {'title': 'Total Patients', 'value': stats['total_patients']},
        {'title': 'Active Doctors', 'value': stats['total_doctors']},
        {'title': "Today's Appointments", 'value': stats['today_appointments']},
        {'title': 'Pending Appointments', 'value': stats['pending_appointments']},
        {'title': 'Admitted Patients', 'value': 18},
        {'title': 'In Labor', 'value': stats['in_labor']}
    ]

    appointments = [
        {'patient_name': 'Jane Doe', 'doctor_name': 'Dr. Otieno', 'time': '10:00 AM'},
        {'patient_name': 'John Mwangi', 'doctor_name': 'Dr. Achieng', 'time': '11:30 AM'}
    ]

    return render_template('dashboard.html', stats=stats, stats_grid=stats_grid, appointments=appointments, current_date='September 10, 2025')




@app.route('/release/<int:patient_id>')
def release_summary(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    treatments = db.execute("SELECT * FROM treatments WHERE patient_id = ?", (patient_id,)).fetchall()
    labs = db.execute("SELECT * FROM lab_results WHERE patient_id = ?", (patient_id,)).fetchall()
    prescriptions = db.execute("SELECT * FROM pharmacy_orders WHERE patient_id = ?", (patient_id,)).fetchall()
    billing = db.execute("SELECT SUM(amount) FROM billing WHERE patient_id = ?", (patient_id,)).fetchone()[0]

    return render_template('release.html', patient=patient, treatments=treatments, labs=labs, prescriptions=prescriptions, billing=billing)

# @app.route('/release')
# def release():
#     return render_template('release.html')

# ---------------- Patient Registration ----------------
# from datetime import datetime
# import time



# @app.route('/checkin', methods=['GET', 'POST'])
# def checkin():
#     generated_mrn = f"MRN{int(time.time())}"

#     if request.method == 'POST':
#         card_number = request.form.get('card_number')
#         if not card_number:
#             flash('Please enter a card number.', 'danger')
#             return redirect(url_for('checkin'))

#         db = get_db()
#         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()

#         if patient:
#             # Check if already queued today
#             existing_appt = db.execute("""
#                 SELECT id FROM appointments 
#                 WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
#             """, (patient['id'],)).fetchone()

#             if not existing_appt:
#                 db.execute("""
#                     INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
#                     VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
#                 """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic
#                 db.commit()

#                 try:
#                     sms.send(f"{patient['first_name']} {patient['last_name']} has been queued for doctor review.", [patient['contact']])
#                 except Exception as e:
#                     print("SMS failed:", e)

#             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
#             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
#         else:
#             flash(f"No patient found with card number: {card_number}", 'warning')
#             return redirect(url_for('checkin'))

#     return render_template('checkin.html', generated_mrn=generated_mrn)



# from datetime import datetime
# import time

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()

#     if request.method == 'POST':
#         data = request.form
#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address', 'card_number']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return redirect(url_for('register'))

#         # Check for duplicate contact or card number
#         existing = db.execute("SELECT id FROM patients WHERE contact = ? OR card_number = ?", 
#                               (data['contact'], data['card_number'])).fetchone()
#         if existing:
#             flash('A patient with this contact or card number already exists.', 'warning')
#             return redirect(url_for('register'))

#         full_name = f"{data['first_name']} {data['last_name']}"
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn,
#             data['card_number'],
#             full_name,
#             data['first_name'],
#             data['last_name'],
#             age,
#             data['gender'],
#             data['contact'],
#             data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         flash('Patient registered successfully!', 'success')
#         return redirect(url_for('print_card', patient_id=new_id))

#     # GET request — generate MRN for display
#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card)




# # ......................printcard.............................
# @app.route('/print_card/<int:patient_id>')
# def print_card(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     return render_template('patient_card.html', patient=patient)

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import time

# app = Flask(__name__)

# def get_db():
#     # your DB connection logic here
#     pass


@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    generated_mrn = f"MRN{int(time.time())}"

    if request.method == 'POST':
        card_number = request.form.get('card_number')
        if not card_number:
            flash('Please enter a card number.', 'danger')
            return redirect(url_for('checkin'))

        db = get_db()
        patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()

        if patient:
            # Check if already queued today
            existing_appt = db.execute("""
                SELECT id FROM appointments 
                WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
            """, (patient['id'],)).fetchone()

            if not existing_appt:
                db.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
                    VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
                """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic
                db.commit()

                try:
                    sms.send(f"{patient['first_name']} {patient['last_name']} has been queued for doctor review.", [patient['contact']])
                except Exception as e:
                    print("SMS failed:", e)

            flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
            return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
        else:
            flash(f"No patient found with card number: {card_number}. Please register.", 'warning')
            return redirect(url_for('register'))

    return render_template('checkin.html', generated_mrn=generated_mrn)


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()

#     if request.method == 'POST':
#         data = request.form
#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address', 'card_number']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return redirect(url_for('register'))

#         # Check for duplicate contact or card number
#         existing = db.execute("SELECT id FROM patients WHERE contact = ? OR card_number = ?", 
#                               (data['contact'], data['card_number'])).fetchone()
#         if existing:
#             flash('A patient with this contact or card number already exists.', 'warning')
#             return redirect(url_for('checkin'))

#         full_name = f"{data['first_name']} {data['last_name']}"
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn,
#             data['card_number'],
#             full_name,
#             data['first_name'],
#             data['last_name'],
#             age,
#             data['gender'],
#             data['contact'],
#             data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         # Queue patient for doctor immediately
#         db.execute("""
#             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
#             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
#         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
#         db.commit()

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}. You have been queued for doctor review.", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         flash('Patient registered and queued successfully!', 'success')
#         return redirect(url_for('doctor_dashboard', patient_id=new_id))

#     # GET request — generate MRN for display
#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn)

@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()

    if request.method == 'POST':
        data = request.form
        required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            flash(f"Missing fields: {', '.join(missing)}", 'danger')
            return redirect(url_for('register'))

        try:
            age = int(data['age'])
            if age < 0 or age > 120:
                flash('Please enter a valid age between 0 and 120.', 'warning')
                return redirect(url_for('register'))
        except ValueError:
            flash('Age must be a number.', 'warning')
            return redirect(url_for('register'))

        # Generate card number automatically
        last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
        next_id = (last or 0) + 1
        card_number = f"HCO{next_id:05d}"   # Example: HCO00001, HCO00002, etc.
        mrn = f"MRN{next_id:05d}"

        full_name = f"{data['first_name']} {data['last_name']}"

        cursor = db.execute("""
            INSERT INTO patients (
                medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
                is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            mrn,
            card_number,
            full_name,
            data['first_name'],
            data['last_name'],
            age,
            data['gender'],
            data['contact'],
            data['address']
        ))
        db.commit()
        new_id = cursor.lastrowid

        # Queue patient for doctor immediately
        db.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
            VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
        """, (new_id, 1))
        db.commit()

        flash(f'Patient registered successfully! Card Number: {card_number}', 'success')
        return redirect(url_for('print_card', patient_id=new_id))

    # GET request — generate MRN preview
    generated_mrn = f"MRN{int(time.time())}"
    return render_template('register.html', generated_mrn=generated_mrn)


@app.route('/print_card/<int:patient_id>')
def print_card(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return render_template('patient_card.html', patient=patient)



# ---------------- Doctor Interface ----------------
@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    db = get_db()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        symptoms = request.form['symptoms']
        diagnosis = request.form['diagnosis']
        db.execute("""
            UPDATE patients 
            SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (symptoms, diagnosis, patient_id))
        db.commit()
        flash('Diagnosis saved successfully!')
        return redirect(url_for('doctor'))

    today_patients = db.execute("""
        SELECT patients.id AS patient_id, first_name || ' ' || last_name AS name
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        WHERE DATE(appointments.appointment_date) = DATE('now') AND appointments.status = 'scheduled'
        ORDER BY appointments.appointment_date ASC
    """).fetchall()

    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('doctor.html', patients=today_patients, current_date=current_date)


@app.route('/doctor/examine/<int:patient_id>', methods=['GET', 'POST'])
def examine_patient(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

    if request.method == 'POST':
        symptoms = request.form['symptoms']
        diagnosis = request.form['diagnosis']
        prescriptions = request.form['prescriptions']
        tests = request.form['tests']

        db.execute("""
            UPDATE patients 
            SET symptoms = ?, diagnosis = ?, prescriptions = ?, tests_ordered = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (symptoms, diagnosis, prescriptions, tests, patient_id))
        db.commit()
        flash('Patient updated successfully!')
        return redirect(url_for('doctor'))

    return render_template('examine.html', patient=patient)


@app.route('/doctor/autosave/<int:patient_id>', methods=['POST'])
def autosave(patient_id):
    data = request.get_json()
    db = get_db()
    db.execute("""
        UPDATE patients SET symptoms = ?, diagnosis = ?, prescriptions = ?, tests_ordered = ?, status = 'draft', updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (data['symptoms'], data['diagnosis'], data['prescriptions'], data['tests'], patient_id))
    db.commit()
    return jsonify({'message': 'Draft saved'})


@app.route('/doctor/prescription/<int:patient_id>')
def prescription_pdf(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    html = render_template('prescription_template.html', patient=patient)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=prescription_{patient_id}.pdf'
    return response


@app.route('/lab/order', methods=['POST'])
def order_lab_test():
    patient_id = request.form['patient_id']
    test_name = request.form['test_name']
    db = get_db()
    db.execute("INSERT INTO lab_orders (patient_id, test_name, ordered_by) VALUES (?, ?, ?)",
               (patient_id, test_name, 'Dr. Wanyama'))
    db.commit()
    flash('Lab test ordered successfully')
    return redirect(url_for('doctor'))


@app.route('/doctor/<int:patient_id>')
def doctor_dashboard(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return render_template('doctor_dashboard.html', patient=patient)


# ....................notify.............................
@app.route('/notify_doctor_ready/<int:appointment_id>')
def notify_doctor_ready(appointment_id):
    db = get_db()
    appointment = db.execute("""
        SELECT a.*, d.contact AS doctor_contact, p.first_name || ' ' || p.last_name AS patient_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN patients p ON a.patient_id = p.id
        WHERE a.id = ?
    """, (appointment_id,)).fetchone()

    try:
        sms.send(f"Patient {appointment['patient_name']} is ready for examination.", [appointment['doctor_contact']])
        flash('Doctor notified successfully.', 'success')
    except Exception as e:
        print("SMS failed:", e)
        flash('Failed to notify doctor.', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/doctor_ready/<int:appointment_id>')
def doctor_ready(appointment_id):
    db = get_db()
    appointment = db.execute("""
        SELECT a.*, p.contact AS patient_contact
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.id = ?
    """, (appointment_id,)).fetchone()

    try:
        sms.send(f"Doctor is ready to see you now.", [appointment['patient_contact']])
        flash('Patient notified.', 'success')
    except Exception as e:
        print("SMS failed:", e)
        flash('Failed to notify patient.', 'danger')

    return redirect(url_for('doctor'))


# ....................send to pharmacy.............................
# @app.route('/send_to_pharmacy/<int:patient_id>')
# def send_to_pharmacy(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

#     # Record pharmacy order
#     db.execute("""
#         INSERT INTO pharmacy_orders (patient_id, ordered_by, created_at, status)
#         VALUES (?, ?, CURRENT_TIMESTAMP, 'pending')
#     """, (patient_id, 'Dr. Wanyama'))
#     db.commit()

#     flash(f"Patient {patient['first_name']} {patient['last_name']} sent to pharmacy.", 'success')
#     return redirect(url_for('doctor'))

# Doctor sends patient to pharmacy
@app.route('/send_to_pharmacy/<int:patient_id>')
def send_to_pharmacy(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

    db.execute("""
        INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by, created_at, status)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
    """, (patient_id, patient['prescriptions'], 'Dr. Wanyama'))
    db.commit()

    flash(f"Patient {patient['first_name']} {patient['last_name']} sent to pharmacy.", 'success')
    return redirect(url_for('doctor'))


# Pharmacy dashboard
@app.route('/pharmacy')
def pharmacy():
    db = get_db()
    orders = db.execute("""
        SELECT po.id, p.medical_record_number,
               p.first_name || ' ' || p.last_name AS patient_name,
               po.prescription, po.ordered_by, po.created_at,
               po.status, po.fulfilled_by, po.fulfilled_at
        FROM pharmacy_orders po
        JOIN patients p ON po.patient_id = p.id
        ORDER BY po.created_at DESC
    """).fetchall()

    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('pharmacy.html', orders=orders, current_date=current_date)


@app.route('/pharmacy/fulfill', methods=['POST'])
def fulfill_order():
    order_id = request.form['order_id']
    db = get_db()
    db.execute("""
        UPDATE pharmacy_orders
        SET status = 'fulfilled', fulfilled_by = 'Pharmacist A',
            fulfilled_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (order_id,))
    db.commit()
    flash('Order marked as fulfilled')
    return redirect(url_for('pharmacy_dashboard'))


# Doctor sends patient to lab
@app.route('/send_to_lab/<int:patient_id>', methods=['POST'])
def send_to_lab(patient_id):
    test_name = request.form.get('test_name', 'General Test')
    db = get_db()
    db.execute("""
        INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (patient_id, test_name, 'Dr. Wanyama'))
    db.commit()
    flash('Lab test ordered successfully')
    return redirect(url_for('doctor'))


# Lab dashboard
@app.route('/lab', methods=['GET', 'POST'])
def lab():
    db = get_db()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        lab_results = request.form['lab_results']
        db.execute("""
            UPDATE patients
            SET lab_results = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (lab_results, patient_id))
        db.commit()
        flash('Lab results saved successfully!')
        return redirect(url_for('lab_dashboard'))

    orders = db.execute("""
        SELECT lo.id, p.medical_record_number,
               p.first_name || ' ' || p.last_name AS patient_name,
               lo.test_name, lo.ordered_by, lo.created_at
        FROM lab_orders lo
        JOIN patients p ON lo.patient_id = p.id
        ORDER BY lo.created_at DESC
    """).fetchall()

    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('lab.html', orders=orders, current_date=current_date)




# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     db = get_db()

#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
#         db.execute("""
#             UPDATE patients 
#             SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP 
#             WHERE id = ?
#         """, (symptoms, diagnosis, patient_id))
#         db.commit()
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('doctor'))

#     today_patients = db.execute("""
#         SELECT patients.id AS patient_id, first_name || ' ' || last_name AS name
#         FROM appointments
#         JOIN patients ON appointments.patient_id = patients.id
#         WHERE DATE(appointments.appointment_date) = DATE('now') AND appointments.status = 'scheduled'
#         ORDER BY appointments.appointment_date ASC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('doctor.html', patients=today_patients, current_date=current_date)


# @app.route('/doctor/examine/<int:patient_id>', methods=['GET', 'POST'])
# def examine_patient(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

#     if request.method == 'POST':
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
#         prescriptions = request.form['prescriptions']
#         tests = request.form['tests']

#         db.execute("""
#             UPDATE patients 
#             SET symptoms = ?, diagnosis = ?, prescriptions = ?, tests_ordered = ?, updated_at = CURRENT_TIMESTAMP 
#             WHERE id = ?
#         """, (symptoms, diagnosis, prescriptions, tests, patient_id))
#         db.commit()
#         flash('Patient updated successfully!')
#         return redirect(url_for('doctor'))

#     return render_template('examine.html', patient=patient)


# @app.route('/doctor/autosave/<int:patient_id>', methods=['POST'])
# def autosave(patient_id):
#     data = request.get_json()
#     db = get_db()
#     db.execute("""
#         UPDATE patients SET symptoms = ?, diagnosis = ?, prescriptions = ?, tests_ordered = ?, status = 'draft', updated_at = CURRENT_TIMESTAMP 
#         WHERE id = ?
#     """, (data['symptoms'], data['diagnosis'], data['prescriptions'], data['tests'], patient_id))
#     db.commit()
#     return jsonify({'message': 'Draft saved'})




# @app.route('/doctor/prescription/<int:patient_id>')
# def prescription_pdf(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     html = render_template('prescription_template.html', patient=patient)
#     pdf = HTML(string=html).write_pdf()
#     response = make_response(pdf)
#     response.headers['Content-Type'] = 'application/pdf'
#     response.headers['Content-Disposition'] = f'inline; filename=prescription_{patient_id}.pdf'
#     return response


# @app.route('/lab/order', methods=['POST'])
# def order_lab_test():
#     patient_id = request.form['patient_id']
#     test_name = request.form['test_name']
#     db = get_db()
#     db.execute("INSERT INTO lab_orders (patient_id, test_name, ordered_by) VALUES (?, ?, ?)",
#                (patient_id, test_name, 'Dr. Wanyama'))
#     db.commit()
#     flash('Lab test ordered successfully')
#     return redirect(url_for('doctor'))

# @app.route('/doctor/<int:patient_id>')
# def doctor_dashboard(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     return render_template('doctor_dashboard.html', patient=patient)

# # ....................notify.............................
# @app.route('/notify_doctor_ready/<int:appointment_id>')
# def notify_doctor_ready(appointment_id):
#     db = get_db()
#     appointment = db.execute("""
#         SELECT a.*, d.contact AS doctor_contact, p.first_name || ' ' || p.last_name AS patient_name
#         FROM appointments a
#         JOIN doctors d ON a.doctor_id = d.id
#         JOIN patients p ON a.patient_id = p.id
#         WHERE a.id = ?
#     """, (appointment_id,)).fetchone()

#     try:
#         sms.send(f"Patient {appointment['patient_name']} is ready for examination.", [appointment['doctor_contact']])
#         flash('Doctor notified successfully.', 'success')
#     except Exception as e:
#         print("SMS failed:", e)
#         flash('Failed to notify doctor.', 'danger')

#     return redirect(url_for('dashboard'))



# @app.route('/doctor_ready/<int:appointment_id>')
# def doctor_ready(appointment_id):
#     db = get_db()
#     appointment = db.execute("""
#         SELECT a.*, p.contact AS patient_contact
#         FROM appointments a
#         JOIN patients p ON a.patient_id = p.id
#         WHERE a.id = ?
#     """, (appointment_id,)).fetchone()

#     try:
#         sms.send(f"Doctor is ready to see you now.", [appointment['patient_contact']])
#         flash('Patient notified.', 'success')
#     except Exception as e:
#         print("SMS failed:", e)
#         flash('Failed to notify patient.', 'danger')

#     return redirect(url_for('doctor'))

# ---------------- Laboratory ----------------
# from functools import wraps
# from flask import abort
# from flask_login import current_user

# @app.route('/lab', methods=['GET', 'POST'])
# def lab():
#     db = get_db()

#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         lab_results = request.form['lab_results']
#         db.execute("UPDATE patients SET lab_results = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
#                    (lab_results, patient_id))
#         db.commit()
#         flash('Lab results saved successfully!')
#         return redirect(url_for('lab'))

#     patients = db.execute("SELECT id, first_name || ' ' || last_name AS name FROM patients").fetchall()
#     recent_entries = db.execute("""
#         SELECT patients.first_name || ' ' || patients.last_name AS name,
#                patients.lab_results,
#                patients.updated_at
#         FROM patients
#         WHERE lab_results IS NOT NULL
#         ORDER BY updated_at DESC
#         LIMIT 10
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('lab.html', patients=patients, recent_entries=recent_entries, current_date=current_date)


# # ---------------- Pharmacy ----------------
# @app.route('/pharmacy', methods=['GET', 'POST'])
# def pharmacy():
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         prescribed_medicine = request.form['prescribed_medicine']
#         db = get_db()
#         db.execute("UPDATE patients SET prescribed_medicine = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
#                    (prescribed_medicine, patient_id))
#         db.commit()
#         flash('Prescribed medicine saved successfully!')
#         return redirect(url_for('pharmacy'))
#     return render_template('pharmacy.html')


# @app.route('/pharmacy/order', methods=['POST'])
# def pharmacy_order():
#     patient_id = request.form['patient_id']
#     prescription = request.form['prescription']
#     ordered_by = 'Dr. Wanyama'  # Replace with session user if using login
#     db = get_db()
#     db.execute("""
#         INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by)
#         VALUES (?, ?, ?)
#     """, (patient_id, prescription, ordered_by))
#     db.commit()
#     flash('Prescription sent to pharmacy')
#     return redirect(url_for('doctor'))


# @app.route('/pharmacy')
# def pharmacy_dashboard():
#     db = get_db()
#     orders = db.execute("""
#         SELECT po.*, p.first_name || ' ' || p.last_name AS patient_name
#         FROM pharmacy_orders po
#         JOIN patients p ON po.patient_id = p.id
#         ORDER BY po.created_at DESC
#     """).fetchall()
#     return render_template('pharmacy.html', orders=orders)


# @app.route('/pharmacy/fulfill', methods=['POST'])
# def fulfill_order():
#     order_id = request.form['order_id']
#     db = get_db()
#     db.execute("""
#         UPDATE pharmacy_orders 
#         SET status = 'fulfilled', fulfilled_by = 'Pharmacist A', fulfilled_at = CURRENT_TIMESTAMP 
#         WHERE id = ?
#     """, (order_id,))
#     db.commit()
#     flash('Order marked as fulfilled')
#     return redirect(url_for('pharmacy_dashboard'))



# .....................Labor.....................



# ---------------- Labor & Delivery Dashboard ----------------
@app.route('/labor_delivery')
def labor_delivery_dashboard():
    db = get_db()
    records = db.execute('SELECT * FROM labor_records WHERE status="active"').fetchall()
    delivered_today = db.execute('SELECT COUNT(*) FROM labor_records WHERE status="delivered" AND DATE(delivery_time)=DATE("now")').fetchone()[0]
    avg_labor = db.execute('SELECT AVG(duration) FROM labor_records WHERE duration IS NOT NULL').fetchone()[0] or 0

    metrics = {
        'in_labor': len(records),
        'delivered_today': delivered_today,
        'maternity_beds': db.execute("SELECT COUNT(*) FROM beds WHERE ward = 'maternity'").fetchone()[0],
        'avg_labor': round(avg_labor, 1)
    }

    return render_template('labor_delivery.html', metrics=metrics, records=records)

# ---------------- Start Labor Record ----------------
@app.route('/labor_delivery/start', methods=['POST'])
def start_labor_record():
    db = get_db()
    patient_name = request.form['patient_name']
    db.execute('INSERT INTO labor_records (patient_name, start_time, status) VALUES (?, ?, ?)',
               (patient_name, datetime.now(), 'active'))
    db.commit()
    flash('Labor record started successfully!')
    return redirect(url_for('labor_delivery_dashboard'))

# ---------------- Complete Labor Record ----------------
@app.route('/labor_delivery/complete', methods=['POST'])
def complete_labor_record():
    record_id = request.form['record_id']
    db = get_db()
    record = db.execute("SELECT start_time FROM labor_records WHERE id = ?", (record_id,)).fetchone()

    if record:
        start_time = datetime.fromisoformat(record['start_time'])
        delivery_time = datetime.now()
        duration = round((delivery_time - start_time).total_seconds() / 3600, 2)

        db.execute("""
            UPDATE labor_records
            SET delivery_time = ?, duration = ?, status = 'delivered'
            WHERE id = ?
        """, (delivery_time, duration, record_id))
        db.commit()
        flash('Labor marked as delivered successfully!')

    return redirect(url_for('labor_delivery_dashboard'))

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


@app.route('/patient/<int:id>')
def patient_detail(id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
    db.close()

    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for('checkin'))

    return render_template('patient_detail.html', patient=patient)


# ---------------- Patient List ----------------
@app.route('/patients')
def patients():
    db = get_db()
    patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
    return render_template('patients.html', patients=patients)

# ---------------- Additional Sidebar Routes ----------------
@app.route('/admission')
def admission():
    return render_template('admission.html')

@app.route('/labor_delivery')
def labor_delivery():
    return render_template('labor_delivery.html')

@app.route('/appointments')
def appointments():
    db = get_db()
    appointments = db.execute("""
        SELECT a.*, 
               p.first_name || ' ' || p.last_name AS patient_name,
               d.first_name || ' ' || d.last_name AS doctor_name,
               strftime('%H:%M', a.appointment_date) AS time
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.appointment_date ASC
    """).fetchall()
    return render_template('appointments.html', appointments=appointments)

@app.route('/medical_reports')
def medical_reports():
    return render_template('medical_reports.html')

# ---------------- Search ----------------
@app.route('/search', methods=['GET', 'POST'])
def search():
    db = get_db()
    results = []

    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        status = request.form.get('status', '').strip()
        date = request.form.get('date', '').strip()

        sql = "SELECT * FROM patients WHERE 1=1"
        params = []

        if query:
            sql += " AND (first_name LIKE ? OR last_name LIKE ? OR contact LIKE ? OR medical_record_number LIKE ?)"
            params += [f'%{query}%'] * 4

        if status:
            sql += " AND admission_status = ?"
            params.append(status)

        if date:
            sql += " AND DATE(created_at) = ?"
            params.append(date)

        sql += " ORDER BY created_at DESC"
        results = db.execute(sql, params).fetchall()

    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, port=5001)





# @app.route('/checkin', methods=['GET', 'POST'])
# def checkin():
#     generated_mrn = f"MRN{int(time.time())}"  # Used for new patient registration modal

#     if request.method == 'POST':
#         card_number = request.form.get('card_number')
#         if not card_number:
#             flash('Please enter a card number.', 'danger')
#             return redirect(url_for('checkin'))

#         db = get_db()
#         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()
#         db.close()

#         if patient:
#             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
#             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
#         else:
#             flash(f"Patient Not Found - No patient found with card number: {card_number}", 'warning')
#             return redirect(url_for('checkin'))

#     # GET request — show check-in page with generated MRN
#     return render_template('checkin.html', generated_mrn=generated_mrn)


# return render_template('register.html', generated_mrn=generated_mrn)

# from datetime import datetime
# import time

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()

#     if request.method == 'POST':
#         data = request.form

#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return redirect(url_for('register'))

#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.', 'warning')
#             return redirect(url_for('register'))

#         full_name = f"{data['first_name']} {data['last_name']}"
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn,
#             full_name,
#             data['first_name'],
#             data['last_name'],
#             age,
#             data['gender'],
#             data['contact'],
#             data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         flash('Patient registered successfully!', 'success')
#         return redirect(url_for('register', show_modal='true', patient_id=new_id))

#     # GET request — generate MRN for display
#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn, patient_card=None)


#  @app.route('/print_card/<int:patient_id>')
# def print_card(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     return render_template('patient_card.html', patient=patient)

# @app.route('/print_card/<int:patient_id>')
# def print_card(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     return render_template('patient_card.html', patient=patient)

# @app.route('/checkin', methods=['GET', 'POST'])
# def checkin():
#     generated_mrn = f"MRN{int(time.time())}"

#     if request.method == 'POST':
#         card_number = request.form.get('card_number')
#         if not card_number:
#             flash('Please enter a card number.', 'danger')
#             return redirect(url_for('checkin'))

#         db = get_db()
#         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()

#         if patient:
#             # Queue if not already
#             existing_appt = db.execute("""
#                 SELECT id FROM appointments WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
#             """, (patient['id'],)).fetchone()

#             if not existing_appt:
#                 db.execute("""
#                     INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
#                     VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
#                 """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic
#                 db.commit()

#             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
#             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
#         else:
#             flash(f"No patient found with card number: {card_number}", 'warning')
#             return redirect(url_for('checkin'))

#     return render_template('checkin.html', generated_mrn=generated_mrn)





# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     db = get_db()

#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
#         db.execute("""
#             UPDATE patients 
#             SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP 
#             WHERE id = ?
#         """, (symptoms, diagnosis, patient_id))
#         db.commit()
#         flash('Diagnosis saved successfully!')
#         return redirect(url_for('doctor'))

#     # Fetch today's patients (example logic)
#     today_patients = db.execute("""
#     SELECT patients.id AS patient_id,
#            first_name || ' ' || last_name AS name 
#     FROM appointments 
#     JOIN patients ON appointments.patient_id = patients.id 
#     WHERE DATE(appointments.appointment_date) = DATE('now')
# """).fetchall()


#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('doctor.html', patients=today_patients, current_date=current_date)




# from datetime import datetime
# import time

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()
#     patient_card = None  # ✅ Define it early so it's available in both GET and POST

#     if request.method == 'POST':
#         data = request.form
#         required_fields = ['first_name', 'last_name', 'dob', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]

#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         try:
#             dob = datetime.strptime(data['dob'], '%Y-%m-%d')
#             today = datetime.today()
#             age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
#             if age < 0 or age > 120:
#                 flash('Please enter a valid date of birth.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Date of birth must be in YYYY-MM-DD format.', 'warning')
#             return redirect(url_for('register'))

#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.', 'warning')
#             return redirect(url_for('register'))

#         full_name = f"{data['first_name']} {data['last_name']}"
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn, full_name, data['first_name'], data['last_name'], age,
#             data['gender'], data['contact'], data['address']
#         ))
#         db.commit()

#         new_id = cursor.lastrowid

#         db.execute("""
#             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
#             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
#         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
#         db.commit()

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         patient_card = db.execute("SELECT * FROM patients WHERE id = ?", (new_id,)).fetchone()
#         flash('Patient registered and queued successfully!', 'success')
#         return render_template('register.html', generated_mrn=mrn, patient_card=patient_card, show_modal='true')

#     # GET request — show empty registration form
#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card)


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()

#     if request.method == 'POST':
#         data = request.form
#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return redirect(url_for('register'))

#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.', 'warning')
#             return redirect(url_for('register'))

#         full_name = f"{data['first_name']} {data['last_name']}"
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn, full_name, data['first_name'], data['last_name'], age,
#             data['gender'], data['contact'], data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         # Queue patient to doctor
#         db.execute("""
#             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
#             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
#         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
#         db.commit()

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         patient_card = db.execute("SELECT * FROM patients WHERE id = ?", (new_id,)).fetchone()
#         flash('Patient registered and queued successfully!', 'success')
#         return render_template('register.html', generated_mrn=mrn, patient_card=patient_card, show_modal='true')

#     # GET request — show empty registration form
#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card)

    # return render_template('register.html', generated_mrn=generated_mrn)

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()

#     if request.method == 'POST':
#         data = request.form
#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return redirect(url_for('register'))

#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.', 'warning')
#             return redirect(url_for('register'))

#         full_name = f"{data['first_name']} {data['last_name']}"
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn, full_name, data['first_name'], data['last_name'], age,
#             data['gender'], data['contact'], data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         # Queue patient to doctor
#         db.execute("""
#             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
#             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
#         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
#         db.commit()

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         flash('Patient registered and queued successfully!', 'success')
#         return redirect(url_for('print_card', patient_id=new_id))

#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn)
#     patient_card = db.execute("SELECT * FROM patients WHERE id = ?", (new_id,)).fetchone()
#     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card, show_modal='true')



# from datetime import datetime
# import time

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()

#     if request.method == 'POST':
#         data = request.form

#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return redirect(url_for('register'))

#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.', 'warning')
#             return redirect(url_for('register'))

#         full_name = f"{data['first_name']} {data['last_name']}"

#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn,
#             data['first_name'],
#             data['last_name'],
#             age,
#             data['gender'],
#             data['contact'],
#             data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         # flash('Patient registered successfully!', 'success')
#         # return redirect(url_for('doctor_dashboard', patient_id=new_id))
#         flash('Patient registered successfully!', 'success')
#         return redirect(url_for('register', show_modal='true', patient_id=new_id))


#     # GET request — generate MRN for display
#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn, patient_card=None)
# @app.route('/checkin', methods=['GET', 'POST'])
# def checkin():
#     ...
#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('checkin.html', generated_mrn=generated_mrn)

# @app.route('/checkin', methods=['GET', 'POST'])
# def checkin():
#     if request.method == 'POST':
#         card_number = request.form.get('card_number')
#         if not card_number:
#             flash('Please enter a card number.', 'danger')
#             return redirect(url_for('checkin'))

#         db = get_db()
#         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()
#         db.close()

#         if patient:
#             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
#             # Redirect to doctor dashboard with patient ID
#             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
#         else:
#             flash(f"Patient Not Found - No patient found with card number: {card_number}", 'warning')
#             return redirect(url_for('checkin'))

#     return render_template('checkin.html')





# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     db = get_db()
#     generated_mrn = f"MRN{int(time.time())}"  # Default MRN for GET

#     if request.method == 'POST':
#         data = request.form
#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]

#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return render_template('checkin.html', generated_mrn=generated_mrn)

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return render_template('checkin.html', generated_mrn=generated_mrn)
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return render_template('checkin.html', generated_mrn=generated_mrn)

#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.', 'warning')
#             return render_template('checkin.html', generated_mrn=generated_mrn)

#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn, data['first_name'], data['last_name'], age,
#             data['gender'], data['contact'], data['address']
#         ))
#         db.commit()

#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         flash(f'Patient registered successfully! MRN: {mrn}', 'success')
#         return render_template('checkin.html', generated_mrn=mrn)

#     return render_template('checkin.html', generated_mrn=generated_mrn)




# @app.route('/checkin', methods=['GET', 'POST'])
# def checkin():
#     if request.method == 'POST':
#         card_number = request.form.get('card_number')
#         if not card_number:
#             flash('Please enter a card number.', 'danger')
#             return redirect(url_for('checkin'))

#         db = get_db()
#         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()
#         db.close()

#         if patient:
#             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
#         else:
#             flash('No patient found with that card number.', 'warning')

#         return redirect(url_for('checkin'))

#     return render_template('checkin.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         data = request.form
#         db = get_db()

#         # Validate required fields
#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}", 'danger')
#             return redirect(url_for('register'))

#         # Validate age
#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.', 'warning')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.', 'warning')
#             return redirect(url_for('register'))

#         # Check for duplicate contact
#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.', 'warning')
#             return redirect(url_for('register'))

#         # Generate MRN
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         # Insert patient
#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn,
#             data['first_name'],
#             data['last_name'],
#             age,
#             data['gender'],
#             data['contact'],
#             data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         # Optional: Send SMS
#         try:
#             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         flash('Patient registered successfully!', 'success')
#         return redirect(url_for('patient_detail', id=new_id))

#     return render_template('register.html')


    # @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         data = request.form
#         db = get_db()

#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}")
#             return redirect(url_for('register'))

#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.')
#             return redirect(url_for('register'))

#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.')
#             return redirect(url_for('register'))

#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, first_name, last_name, age, gender, contact, address,
#                 is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn,
#             data['first_name'],
#             data['last_name'],
#             age,
#             data['gender'],
#             data['contact'],
#             data['address']
#         ))
#         db.commit()
#         new_id = cursor.lastrowid

#         try:
#             sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])
#         except Exception as e:
#             print("SMS failed:", e)

#         flash('Patient registered successfully!')
#         return redirect(url_for('patient_detail', id=new_id))

#     return render_template('register.html')

# if __name__ == '__main__':
#     app.run(debug=True)


# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3
# from datetime import datetime
# import africastalking

# # Initialize SDK
# africastalking.initialize(username="your_username", api_key="your_api_key")
# sms = africastalking.SMS

# # Send SMS
# sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])


# app = Flask(__name__)
# app.secret_key = 'supersecretkey'

# # ---------------- Database Connection ----------------
# def get_db():
#     conn = sqlite3.connect('hospital.db')
#     conn.row_factory = sqlite3.Row
#     return conn

# # ---------------- Dashboard ----------------
# @app.route('/')
# def dashboard():
#     db = get_db()
#     today_sql = datetime.now().strftime('%Y-%m-%d')
#     today_display = datetime.now().strftime('%A, %B %d, %Y')

#     stats = {
#         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
#         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
#         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
#         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
#         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today_sql,)).fetchone()[0],
#         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
#         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
#         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
#         'efficiency': 0
#     }

#     if stats['today_appointments'] > 0:
#         stats['efficiency'] = round((stats['completed_appointments_today'] / stats['today_appointments']) * 100, 2)

#     appointments = db.execute("""
#         SELECT a.*, 
#                p.first_name || ' ' || p.last_name AS patient_name,
#                d.first_name || ' ' || d.last_name AS doctor_name,
#                strftime('%H:%M', a.appointment_date) AS time
#         FROM appointments a
#         JOIN patients p ON a.patient_id = p.id
#         JOIN doctors d ON a.doctor_id = d.id
#         WHERE DATE(a.appointment_date) = ?
#         ORDER BY a.appointment_date ASC
#     """, (today_sql,)).fetchall()

#     return render_template('dashboard.html', stats=stats, appointments=appointments, current_date=today_display)

# # ---------------- Patient Registration ----------------

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         data = request.form
#         db = get_db()

#         # Required field check
#         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
#         missing = [field for field in required_fields if not data.get(field)]
#         if missing:
#             flash(f"Missing fields: {', '.join(missing)}")
#             return redirect(url_for('register'))

#         # Age validation
#         try:
#             age = int(data['age'])
#             if age < 0 or age > 120:
#                 flash('Please enter a valid age between 0 and 120.')
#                 return redirect(url_for('register'))
#         except ValueError:
#             flash('Age must be a number.')
#             return redirect(url_for('register'))

#         # Duplicate contact check
#         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
#         if existing:
#             flash('A patient with this contact already exists.')
#             return redirect(url_for('register'))

#         # Generate MRN
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         mrn = f"MRN{next_id:05d}"

#         # Insert patient

#         # Insert patient
# cursor = db.execute("""
#     INSERT INTO patients (
#         medical_record_number, first_name, last_name, age, gender, contact, address,
#         is_active, created_at, updated_at
#     ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# """, (
#     mrn,
#     data['first_name'],
#     data['last_name'],
#     age,
#     data['gender'],
#     data['contact'],
#     data['address']
# ))
# db.commit()
# new_id = cursor.lastrowid

# # ✅ Send SMS inside the route
# try:
#     sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])
# except Exception as e:
#     print("SMS failed:", e)

# flash('Patient registered successfully!')
# return redirect(url_for('patient_detail', id=new_id))



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

# # ---------------- Laboratory ----------------
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

# # ---------------- Additional Sidebar Routes ----------------
# @app.route('/admission')
# def admission():
#     return render_template('admission.html')

# @app.route('/labor-delivery')
# def labor_delivery():
#     return render_template('labor_delivery.html')

# @app.route('/appointments')
# def appointments():
#     db = get_db()
#     appointments = db.execute("""
#         SELECT a.*, 
#                p.first_name || ' ' || p.last_name AS patient_name,
#                d.first_name || ' ' || d.last_name AS doctor_name,
#                strftime('%H:%M', a.appointment_date) AS time
#         FROM appointments a
#         JOIN patients p ON a.patient_id = p.id
#         JOIN doctors d ON a.doctor_id = d.id
#         ORDER BY a.appointment_date ASC
#     """).fetchall()
#     return render_template('appointments.html', appointments=appointments)

# @app.route('/medical-reports')
# def medical_reports():
#     return render_template('medical_reports.html')


# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     db = get_db()
#     results = []

#     if request.method == 'POST':
#         query = request.form.get('query', '').strip()
#         status = request.form.get('status', '').strip()
#         date = request.form.get('date', '').strip()

#         sql = "SELECT * FROM patients WHERE 1=1"
#         params = []

#         if query:
#             sql += " AND (first_name LIKE ? OR last_name LIKE ? OR contact LIKE ? OR medical_record_number LIKE ?)"
#             params += [f'%{query}%'] * 4
#         if status:
#             sql += " AND admission_status = ?"
#             params.append(status)
#         if date:
#             sql += " AND DATE(created_at) = ?"
#             params.append(date)

#         results = db.execute(sql + " ORDER BY created_at DESC", params).fetchall()

#     return render_template('search.html', results=results)

    #     cursor = db.execute("""
    #         INSERT INTO patients (
    #             medical_record_number, first_name, last_name, age, gender, contact, address,
    #             is_active, created_at, updated_at
    #         ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    #     """, (
    #         mrn,
    #         data['first_name'],
    #         data['last_name'],
    #         age,
    #         data['gender'],
    #         data['contact'],
    #         data['address']
    #     ))
    #     db.commit()
    #     new_id = cursor.lastrowid

    #     # Optional: Send SMS
    #     # sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])

    #     flash('Patient registered successfully!')
    #     return redirect(url_for('patient_detail', id=new_id))

    # return render_template('register.html')

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
#     today_sql = datetime.now().strftime('%Y-%m-%d')
#     today_display = datetime.now().strftime('%A, %B %d, %Y')

#     stats = {
#         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
#         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
#         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
#         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
#         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today_sql,)).fetchone()[0],
#         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
#         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
#         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
#         'efficiency': 0  # You can calculate this based on completed vs total appointments
#     }

#     return render_template('dashboard.html', stats=stats, current_date=today_display)

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
#     display_date = datetime.now().strftime('%A, %B %d, %Y')

#     stats = {
#         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
#         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
#         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today,)).fetchone()[0],
#         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
#         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today,)).fetchone()[0],
#         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
#         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
#         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
#         'efficiency': 0  # You can calculate this later
#     }

#     appointments = db.execute("""
#         SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name,
#                d.first_name || ' ' || d.last_name AS doctor_name
#         FROM appointments a
#         JOIN patients p ON a.patient_id = p.id
#         JOIN doctors d ON a.doctor_id = d.id
#         WHERE DATE(a.appointment_date) = ?
#         ORDER BY a.appointment_date ASC
#     """, (today,)).fetchall()

#     return render_template('dashboard.html', stats=stats, appointments=appointments, current_date=display_date)

# # ---------------- Sidebar Routes ----------------
# @app.route('/check-in')
# def check_in():
#     return render_template('check_in.html')

# @app.route('/doctor-interface')
# def doctor_interface():
#     return render_template('doctor_interface.html')

# @app.route('/laboratory')
# def laboratory():
#     return render_template('laboratory.html')

# @app.route('/pharmacy')
# def pharmacy():
#     return render_template('pharmacy.html')

# @app.route('/billing')
# def billing():
#     return render_template('billing.html')

# @app.route('/patients')
# def patients():
#     db = get_db()
#     patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
#     return render_template('patients.html', patients=patients)

# @app.route('/admission')
# def admission():
#     return render_template('admission.html')

# @app.route('/labor-delivery')
# def labor_delivery():
#     return render_template('labor_delivery.html')

# @app.route('/appointments')
# def appointments():
#     db = get_db()
#     appointments = db.execute("""
#         SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name,
#                d.first_name || ' ' || d.last_name AS doctor_name
#         FROM appointments a
#         JOIN patients p ON a.patient_id = p.id
#         JOIN doctors d ON a.doctor_id = d.id
#         ORDER BY a.appointment_date ASC
#     """).fetchall()
#     return render_template('appointments.html', appointments=appointments)

# @app.route('/medical-reports')
# def medical_reports():
#     return render_template('medical_reports.html')

# if __name__ == '__main__':
#     app.run(debug=True)

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



# Subject: Fraud Report – Stolen Funds via Mobile Number

# Dear Sir/Madam,

# I wish to report a case of fraud involving mobile number +2547XXXXXXX. On [date], I was defrauded of KES [amount] through a mobile transaction. I have attached screenshots and transaction details for your review.

# Kindly assist in investigating this matter and taking appropriate action.

# Sincerely, Edmond Barasa Wanyama ID: [Your ID Number] Phone: +254708690307 Email: wanyamaedmond23@gmail.com