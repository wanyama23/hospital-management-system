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

import sqlite3
from flask import g, Flask

app = Flask(__name__)
DATABASE = "your_database.db"   # replace with your actual DB file path

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,   # allows multi-threaded use
            timeout=10                 # waits up to 10s if locked
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# import africastalking
# import os

# # Use "sandbox" for testing, or your production username
# username = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
# api_key = os.getenv("AFRICASTALKING_API_KEY")

# africastalking.initialize(username, api_key)
# sms = africastalking.SMS


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



from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import time


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
            # Get last visit date
            last_visit = db.execute("""
                SELECT MAX(appointment_date) AS last_visit
                FROM appointments
                WHERE patient_id = ?
            """, (patient['id'],)).fetchone()

            # Get last prescription
            last_prescription = db.execute("""
                SELECT prescriptions, updated_at
                FROM patients
                WHERE id = ?
            """, (patient['id'],)).fetchone()

            # Queue patient if not already queued today
            existing_appt = db.execute("""
                SELECT id FROM appointments 
                WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
            """, (patient['id'],)).fetchone()

            if not existing_appt:
                db.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
                    VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
                """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic

                # ✅ Update patient status so doctor sees them
                db.execute("""
                    UPDATE patients SET status='scheduled', updated_at=CURRENT_TIMESTAMP WHERE id=?
                """, (patient['id'],))

                db.commit()

            return render_template(
                'checkin_details.html',
                patient=patient,
                last_visit=last_visit['last_visit'] if last_visit else None,
                last_prescription=last_prescription['prescriptions'] if last_prescription else None,
                generated_mrn=generated_mrn
            )
        else:
            flash(f"No patient found with card number: {card_number}. Please register.", 'warning')
            return redirect(url_for('register'))

    return render_template('checkin.html', generated_mrn=generated_mrn)


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
        card_number = f"HCO{next_id:05d}"
        mrn = f"MRN{next_id:05d}"

        full_name = f"{data['first_name']} {data['last_name']}"

        cursor = db.execute("""
            INSERT INTO patients (
                medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
                status, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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

    generated_mrn = f"MRN{int(time.time())}"
    return render_template('register.html', generated_mrn=generated_mrn)


@app.route('/print_card/<int:patient_id>')
def print_card(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for('register'))

    # Render the patient card template
    return render_template('patient_card.html', patient=patient)



@app.route('/doctor/<int:patient_id>', methods=['GET'])
def doctor_interface(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    medications = db.execute("SELECT * FROM medications").fetchall()
    lab_tests = db.execute("SELECT * FROM lab_tests").fetchall()
    admissions = db.execute("SELECT * FROM admissions").fetchall()

    return render_template(
        'doctor.html',
        patient=patient,
        medications=medications,
        lab_tests=lab_tests,
        admissions=admissions,
        current_date=datetime.now().strftime("%Y-%m-%d %H:%M")
    )


@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    db = get_db()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        symptoms = request.form['symptoms']
        diagnosis = request.form['diagnosis']
        prescriptions = request.form['prescriptions']
        billing_amount = request.form['billing_amount']

        # Update patient status to awaiting_pharmacy
        db.execute("""
            UPDATE patients 
            SET symptoms=?, diagnosis=?, prescriptions=?, status='awaiting_pharmacy',
                billing_amount=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (symptoms, diagnosis, prescriptions, billing_amount, patient_id))

        # Insert pharmacy order
        db.execute("""
            INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by, created_at, status)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
        """, (patient_id, prescriptions, 'Dr. Wanyama'))

        # Insert cashier order
        db.execute("""
            INSERT INTO cashier_orders (patient_id, amount, status)
            VALUES (?, ?, 'pending')
        """, (patient_id, billing_amount))

        db.commit()
        flash('Prescription saved, patient sent to pharmacy and cashier!')
        return redirect(url_for('doctor'))

    patients = db.execute("""
        SELECT id AS patient_id, first_name || ' ' || last_name AS name, status
        FROM patients
        WHERE status IN ('scheduled', 'awaiting_doctor')
        ORDER BY updated_at ASC
    """).fetchall()

    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('doctor.html', patients=patients, current_date=current_date)



@app.route('/doctor/<int:patient_id>')
def doctor_detail(patient_id):
    db = get_db()
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return render_template('doctor.html', patient=patient, current_date=current_date)


@app.route("/examine/<int:patient_id>", methods=["GET", "POST"])
def examine(patient_id):
    db = get_db()

    # Fetch patient record
    patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("doctor"))

    if request.method == "POST":
        # Save examination details
        symptoms = request.form.get("symptoms")
        diagnosis = request.form.get("diagnosis")
        prescriptions = request.form.get("prescriptions")
        tests = request.form.get("tests")

        db.execute("""
            UPDATE patients
            SET symptoms=?, diagnosis=?, prescriptions=?, tests_ordered=?
            WHERE id=?
        """, (symptoms, diagnosis, prescriptions, tests, patient_id))
        db.commit()

        flash("Examination details saved.", "success")
        return redirect(url_for("examine", patient_id=patient_id))

    # 🔑 Fetch available beds for the Admit Patient modal
    available_beds = db.execute("""
        SELECT bed_number, ward
        FROM beds
        WHERE status='available'
        ORDER BY ward, bed_number
    """).fetchall()

    current_date = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "examine.html",
        patient=patient,
        current_date=current_date,
        available_beds=available_beds   # 👈 Pass into template
    )

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
@app.route('/lab/order', methods=['GET', 'POST'])
def order_lab_test():
    db = get_db()
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        test_name = request.form['test_name']
    else:  # GET request
        patient_id = request.args.get('patient_id')
        test_name = request.args.get('test_name', 'General Test')

    db.execute("""
        INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (patient_id, test_name, 'Dr. Wanyama'))
    db.commit()
    flash('Lab test ordered successfully')
    return redirect(url_for('doctor'))




@app.route('/doctor/<int:patient_id>')
def doctor_dashboard(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return render_template('doctor.html', patient=patient)


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


# Doctor sends patient to pharmacy
@app.route("/send_to_pharmacy/<int:patient_id>")
def send_to_pharmacy(patient_id):
    db = get_db()

    # --- Fetch patient record ---
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        flash("Patient record not found.", "danger")
        return redirect(url_for("doctor"))

    # --- Insert pharmacy order ---
    db.execute("""
        INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by, created_at, status)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
    """, (patient_id, patient["prescriptions"], "Dr. Wanyama"))

    # --- Update patient status so they leave doctor queue ---
    db.execute("""
        UPDATE patients
        SET status='pharmacy'
        WHERE id=?
    """, (patient_id,))

    db.commit()

    flash(f"Patient {patient['first_name']} {patient['last_name']} sent to pharmacy.", "success")
    return redirect(url_for("doctor"))

# @app.route('/send_to_pharmacy/<int:patient_id>')
# def send_to_pharmacy(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

#     db.execute("""
#         INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by, created_at, status)
#         VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
#     """, (patient_id, patient['prescriptions'], 'Dr. Wanyama'))
#     db.commit()

#     flash(f"Patient {patient['first_name']} {patient['last_name']} sent to pharmacy.", 'success')
#     return redirect(url_for('doctor'))


# Pharmacy dashboard
# ---------------- PHARMACY ----------------
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

    order = db.execute("""
        SELECT po.patient_id, po.prescription
        FROM pharmacy_orders po
        WHERE po.id=?
    """, (order_id,)).fetchone()

    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("pharmacy"))

    # Mark pharmacy order as fulfilled
    db.execute("""
        UPDATE pharmacy_orders
        SET status='fulfilled', fulfilled_by='Pharmacist A', fulfilled_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (order_id,))

    # ✅ Calculate totals
    med_total = calculate_medication_total(order['prescription'], db)
    lab_total = calculate_lab_total(order['patient_id'], db)
    admission_total = calculate_admission_total(order['patient_id'], db)

    bill_amount = med_total + lab_total + admission_total

    # Insert cashier order
    db.execute("""
        INSERT INTO cashier_orders (patient_id, amount, status, created_at)
        VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
    """, (order['patient_id'], bill_amount))

    db.commit()
    flash(f'Order fulfilled and sent to cashier. Bill: KES {bill_amount}')
    return redirect(url_for('pharmacy'))




# Doctor sends patient to lab

@app.route('/send_to_lab/<int:patient_id>', methods=['POST'])
def send_to_lab(patient_id):
    test_name = request.form.get('test_name', 'General Test')
    db = get_db()
    db.execute("""
        INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at, status)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
    """, (patient_id, test_name, 'Dr. Wanyama'))

    # Update patient status
    db.execute("""
        UPDATE patients SET status='awaiting_lab', updated_at=CURRENT_TIMESTAMP WHERE id=?
    """, (patient_id,))
    db.commit()

    flash('Lab test ordered successfully')
    return redirect(url_for('doctor'))


# Lab dashboard
@app.route('/lab', methods=['GET'])
def lab():
    db = get_db()
    orders = db.execute("""
        SELECT lo.id, p.medical_record_number,
               p.first_name || ' ' || p.last_name AS patient_name,
               lo.test_name, lo.ordered_by, lo.created_at, lo.status
        FROM lab_orders lo
        JOIN patients p ON lo.patient_id = p.id
        WHERE lo.status = 'pending'
        ORDER BY lo.created_at DESC
    """).fetchall()

    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('lab.html', orders=orders, current_date=current_date)


@app.route('/lab/fulfill', methods=['POST'])
def fulfill_lab_order():
    order_id = request.form['order_id']
    lab_results = request.form['lab_results']
    db = get_db()

    patient_id = db.execute("SELECT patient_id FROM lab_orders WHERE id=?", (order_id,)).fetchone()['patient_id']

    # Save results and send back to doctor
    db.execute("""
        UPDATE patients
        SET lab_results=?, status='awaiting_doctor', updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (lab_results, patient_id))

    db.execute("""
        UPDATE lab_orders
        SET status='fulfilled', fulfilled_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (order_id,))
    db.commit()

    flash('Lab results saved and patient sent back to doctor.')
    return redirect(url_for('lab'))



# --- Admissions Route ---
from datetime import datetime

@app.route("/admit_from_exam/<int:patient_id>", methods=["POST"])
def admit_from_exam(patient_id):
    db = get_db()

    ward = request.form.get("ward")
    bed_number = request.form.get("bed_number")
    reason = request.form.get("reason")
    admitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Safety checks ---
    patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("doctor"))

    bed = db.execute("SELECT * FROM beds WHERE bed_number=? AND status='available'", (bed_number,)).fetchone()
    if not bed:
        flash("Selected bed is not available.", "danger")
        return redirect(url_for("doctor"))

    # --- Insert admission record ---
    db.execute("""
        INSERT INTO admissions (patient_id, ward, bed_number, reason, admitted_at, discharged_at, status)
        VALUES (?, ?, ?, ?, ?, NULL, 'admitted')
    """, (patient_id, ward, bed_number, reason, admitted_at))

    # --- Update patient status so they leave doctor queue ---
    db.execute("""
        UPDATE patients
        SET status='admitted', admission_status='admitted'
        WHERE id=?
    """, (patient_id,))

    # --- Update bed status ---
    db.execute("""
        UPDATE beds
        SET status='occupied', patient_id=?
        WHERE bed_number=?
    """, (patient_id, bed_number))

    db.commit()

    flash("Patient admitted successfully!", "success")

    # --- Redirect logic ---
    if ward == "Maternity":
        return redirect(url_for("labor_delivery"))
    else:
        return redirect(url_for("admission"))


@app.route("/labor_delivery")
def labor_delivery():
    db = get_db()

    # Fetch admitted maternity patients
    patients = db.execute("""
        SELECT a.id, p.first_name || ' ' || p.last_name AS patient_name,
               a.bed_number, a.reason, a.admitted_at, a.status
        FROM admissions a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.ward='Maternity' AND a.status='admitted'
        ORDER BY a.admitted_at DESC
    """).fetchall()

    # Fetch occupied maternity beds
    occupied_beds = db.execute("""
        SELECT bed_number, ward, patient_id
        FROM beds
        WHERE ward='Maternity' AND status='occupied'
    """).fetchall()

    # Fetch active labor records
    records = db.execute("""
        SELECT id, patient_id, patient_name, start_time
        FROM labor_records
        WHERE status='active'
        ORDER BY start_time DESC
    """).fetchall()

    # Metrics
    in_labor = db.execute("SELECT COUNT(*) FROM labor_records WHERE status='active'").fetchone()[0]
    delivered_today = db.execute("""
        SELECT COUNT(*) FROM labor_records
        WHERE status='delivered' AND DATE(end_time) = DATE('now')
    """).fetchone()[0]
    maternity_beds = db.execute("""
        SELECT COUNT(*) FROM beds
        WHERE ward='Maternity' AND status='available'
    """).fetchone()[0]
    avg_labor = db.execute("""
        SELECT AVG(julianday(end_time) - julianday(start_time))*24
        FROM labor_records WHERE status='delivered'
    """).fetchone()[0]
    discharged_today = db.execute("""
        SELECT COUNT(*) FROM admissions
        WHERE ward='Maternity' AND status='discharged'
          AND DATE(discharged_at) = DATE('now')
    """).fetchone()[0]

    metrics = {
        "in_labor": in_labor,
        "delivered_today": delivered_today,
        "maternity_beds": maternity_beds,
        "avg_labor": round(avg_labor or 0, 1),
        "discharged_today": discharged_today   # ✅ new metric
    }

    current_date = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "labor_delivery.html",
        patients=patients,
        occupied_beds=occupied_beds,
        records=records,
        current_date=current_date,
        metrics=metrics
    )


@app.route("/start_labor_record", methods=["POST"])
def start_labor_record():
    db = get_db()
    patient_name = request.form["patient_name"]

    # Insert new labor record into your table
    db.execute("""
        INSERT INTO labor_records (patient_name, start_time)
        VALUES (?, datetime('now'))
    """, (patient_name,))
    db.commit()

    flash(f"Labor record started for {patient_name}")
    return redirect(url_for("labor_delivery"))


@app.route("/complete_labor_record", methods=["POST"])
def complete_labor_record():
    db = get_db()
    record_id = request.form["record_id"]

    # Mark labor record as delivered
    db.execute("""
        UPDATE labor_records
        SET end_time = datetime('now'), status = 'delivered'
        WHERE id = ?
    """, (record_id,))

    # Find patient_id from labor record
    record = db.execute("SELECT patient_id FROM labor_records WHERE id=?", (record_id,)).fetchone()
    if record:
        patient_id = record["patient_id"]

        # Find admission record for this patient in Maternity
        admission = db.execute("""
            SELECT bed_number FROM admissions
            WHERE ward='Maternity' AND status='admitted' AND patient_id=?
        """, (patient_id,)).fetchone()

        if admission:
            bed_number = admission["bed_number"]

            # Free up the bed
            db.execute("""
                UPDATE beds
                SET status='available', patient_id=NULL
                WHERE bed_number=? AND ward='Maternity'
            """, (bed_number,))

            # Mark admission as discharged
            db.execute("""
                UPDATE admissions
                SET status='discharged', discharged_at=datetime('now')
                WHERE patient_id=? AND ward='Maternity'
            """, (patient_id,))

    db.commit()

    flash("Labor record marked as delivered, bed freed, and admission discharged.")
    return redirect(url_for("labor_delivery"))



@app.route("/admit_to_labor/<int:patient_id>", methods=["POST"])
def admit_to_labor(patient_id):
    db = get_db()

    ward = "Labor Ward"  # fixed ward name
    bed_number = request.form.get("bed_number")
    reason = request.form.get("reason")
    admitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Safety checks ---
    patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("doctor"))

    bed = db.execute("SELECT * FROM beds WHERE bed_number=? AND status='available'", (bed_number,)).fetchone()
    if not bed:
        flash("Selected bed is not available.", "danger")
        return redirect(url_for("doctor"))

    # --- Insert labor admission record ---
    db.execute("""
        INSERT INTO labor_admissions (patient_id, ward, bed_number, reason, admitted_at, discharged_at, status)
        VALUES (?, ?, ?, ?, ?, NULL, 'admitted')
    """, (patient_id, ward, bed_number, reason, admitted_at))

    # --- Update patient status so they leave doctor queue ---
    db.execute("""
        UPDATE patients
        SET status='labor', admission_status='admitted'
        WHERE id=?
    """, (patient_id,))

    # --- Update bed status ---
    db.execute("""
        UPDATE beds
        SET status='occupied', patient_id=?
        WHERE bed_number=?
    """, (patient_id, bed_number))

    db.commit()

    flash("Patient admitted to Labor Ward successfully!", "success")
    return redirect(url_for("labor_delivery"))



# --- Admissions Route ---
def calculate_ward_fee(admission, db):
    """
    Calculate the ward fee for a given admission row.
    Works safely with sqlite3.Row by converting to dict first.
    """

    # Convert sqlite3.Row to dict so we can use .get()
    admission = dict(admission)

    # --- Admission date ---
    admission_date_str = admission.get("admission_date") or admission.get("admitted_on")
    admission_date = datetime.strptime(admission_date_str, "%Y-%m-%d") if admission_date_str else datetime.now()

    # --- Discharge date ---
    discharge_date_str = admission.get("discharge_date") or admission.get("released_on")
    discharge_date = datetime.strptime(discharge_date_str, "%Y-%m-%d") if discharge_date_str else datetime.now()

    # --- Days stayed ---
    days_stayed = (discharge_date - admission_date).days
    if days_stayed <= 0:
        days_stayed = 1

    # --- Ward type ---
    ward_type = (admission.get("ward_type") or "general").lower()

    ward_rates = {
        "general": 1000,
        "semi_private": 2000,
        "private": 3000,
        "icu": 5000
    }

    daily_rate = ward_rates.get(ward_type, ward_rates["general"])
    ward_fee = days_stayed * daily_rate

    # --- Optional: add services ---
    try:
        services = db.execute(
            "SELECT cost FROM services WHERE admission_id = ?", (admission["id"],)
        ).fetchall()
        for service in services:
            # Convert each service row to dict before accessing
            service_dict = dict(service)
            ward_fee += service_dict.get("cost", 0)
    except Exception:
        pass

    return ward_fee





@app.route("/admission", methods=["GET", "POST"])
def admission():
    db = get_db()

    if request.method == "POST":
        patient_id = request.form["patient_id"].strip()
        ward = request.form["ward"]
        bed_number = request.form["bed_number"]
        reason = request.form["reason"]
        admitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Safety checks
        patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        if not patient:
            flash("Patient ID not found. Please register the patient first.", "danger")
            return redirect(url_for("admission"))

        bed = db.execute("SELECT * FROM beds WHERE bed_number=? AND status='available'", (bed_number,)).fetchone()
        if not bed:
            flash("Selected bed is not available.", "danger")
            return redirect(url_for("admission"))

        # Insert admission record
        db.execute("""
            INSERT INTO admissions (patient_id, ward, bed_number, reason, admitted_at, discharged_at, status)
            VALUES (?, ?, ?, ?, ?, NULL, 'admitted')
        """, (patient_id, ward, bed_number, reason, admitted_at))

        # Update patient admission_status
        db.execute("UPDATE patients SET admission_status='admitted' WHERE id=?", (patient_id,))

        # Update bed status to occupied
        db.execute("UPDATE beds SET status='occupied', patient_id=? WHERE bed_number=?", (patient_id, bed_number))

        db.commit()
        flash("Patient admitted successfully!", "success")
        return redirect(url_for("admission"))

    # Current admissions
    admissions = db.execute("""
        SELECT a.id,
               p.name AS patient_name,
               a.ward, a.bed_number, a.reason, a.admitted_at, a.status
        FROM admissions a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.status='admitted'
        ORDER BY a.admitted_at DESC
    """).fetchall()

    # Beds list
    beds = db.execute("""
        SELECT bed_number, ward
        FROM beds
        WHERE status='available'
        ORDER BY ward, bed_number
    """).fetchall()

    # Metrics
    admitted_count = db.execute("SELECT COUNT(*) FROM admissions WHERE status='admitted'").fetchone()[0]
    available_beds = db.execute("SELECT COUNT(*) FROM beds WHERE status='available'").fetchone()[0]
    todays_admissions = db.execute("SELECT COUNT(*) FROM admissions WHERE DATE(admitted_at)=DATE('now')").fetchone()[0]
    avg_stay = db.execute("""
        SELECT AVG(julianday(discharged_at) - julianday(admitted_at))
        FROM admissions WHERE status='discharged'
    """).fetchone()[0] or 0

    return render_template(
        "admission.html",
        admissions=admissions,
        beds=beds,
        admitted_count=admitted_count,
        available_beds=available_beds,
        todays_admissions=todays_admissions,
        avg_stay=round(avg_stay, 1)
    )



# --- Discharge Route ---
@app.route("/discharge/<int:admission_id>", methods=["POST"])
def discharge(admission_id):
    db = get_db()

    # Fetch admission row
    admission_row = db.execute(
        "SELECT * FROM admissions WHERE id=?", (admission_id,)
    ).fetchone()

    if not admission_row:
        flash("Admission record not found.", "danger")
        return redirect(url_for("admission"))

    # Convert sqlite3.Row to dict immediately
    admission = dict(admission_row)

    patient_id = admission["patient_id"]
    bed_number = admission["bed_number"]

    # --- Mark admission as discharged ---
    db.execute("""
        UPDATE admissions
        SET status='discharged', discharged_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (admission_id,))

    # --- Free up bed ---
    db.execute(
        "UPDATE beds SET status='available', patient_id=NULL WHERE bed_number=?",
        (bed_number,)
    )

    # --- Reset patient admission_status ---
    db.execute(
        "UPDATE patients SET admission_status='not_admitted' WHERE id=?",
        (patient_id,)
    )

    # --- Calculate billing totals ---
    ward_fee = calculate_ward_fee(admission, db)
    lab_total = calculate_lab_total(patient_id, db)
    med_total = calculate_medication_total(patient_id, db)
    total_amount = ward_fee + lab_total + med_total

    # --- Insert billing record ---
    db.execute("""
        INSERT INTO billing (admission_id, patient_id, ward_fee, lab_total, med_total, total_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """, (admission_id, patient_id, ward_fee, lab_total, med_total, total_amount))

    db.commit()

    flash("Patient discharged and sent to cashier for billing.", "success")
    return redirect(url_for("cashier_detail", admission_id=admission_id))


@app.route("/cashier")
def cashier():
    db = get_db()
    orders = db.execute("""
        SELECT co.id, co.patient_id, co.amount, co.status,
               p.name AS patient_name,
               p.medical_record_number,
               p.card_number
        FROM cashier_orders co
        JOIN patients p ON co.patient_id = p.id
        WHERE co.status='pending'
    """).fetchall()

    return render_template(
        "cashier.html",
        orders=orders,
        current_date=datetime.now().strftime("%Y-%m-%d")
    )






def calculate_ward_fee_from_row(admission_row):
    ward_name = admission_row["ward"]
    ward_fees = {"General": 500, "Maternity": 1000, "ICU": 2000}
    return ward_fees.get(ward_name, 0)




@app.route("/cashier/<int:admission_id>")
def cashier_detail(admission_id):
    db = get_db()  # ✅ define db inside the route

    # Fetch admission record once
    admission_row = db.execute(
        "SELECT * FROM admissions WHERE id=?", (admission_id,)
    ).fetchone()

    if not admission_row:
        return redirect(url_for("admission"))

    patient_id = admission_row["patient_id"]

    # Use the already-fetched row
    ward_fee = calculate_ward_fee_from_row(admission_row)
    lab_total = calculate_lab_total(patient_id, db)
    med_total = calculate_medication_total(patient_id, db)

    total_amount = ward_fee + lab_total + med_total

    db.execute(
        "UPDATE billing SET total_amount=? WHERE admission_id=?",
        (total_amount, admission_id),
    )
    db.commit()

    return render_template(
        "cashier.html",
        admission=admission_row,
        ward_fee=ward_fee,
        lab_total=lab_total,
        med_total=med_total,
        total_amount=total_amount,
    )



@app.route("/cashier/mark_paid/<int:patient_id>", methods=["POST"])
def mark_paid(patient_id):
    db = get_db()
    order_id = request.form.get("order_id")

    # --- Fetch patient record ---
    patient_row = db.execute(
        "SELECT * FROM patients WHERE id=?", (patient_id,)
    ).fetchone()

    if not patient_row:
        flash("Patient record not found.", "danger")
        return redirect(url_for("cashier"))

    patient = dict(patient_row)

    # --- Safely calculate totals ---
    med_total = calculate_medication_total(patient_id, db)
    lab_total = calculate_lab_total(patient_id, db)
    admission_total = calculate_admission_total(patient_id, db)

    total_amount = med_total + lab_total + admission_total

    # --- Update cashier_orders ---
    db.execute("""
        UPDATE cashier_orders
        SET status='paid', amount=?
        WHERE id=? AND patient_id=?
    """, (total_amount, order_id, patient_id))

    # --- Update billing with timestamp ---
    db.execute("""
        UPDATE billing
        SET status='paid', total_amount=?, date_paid=CURRENT_TIMESTAMP
        WHERE patient_id=?
    """, (total_amount, patient_id))

    db.commit()

    flash(f"Payment recorded. Receipt generated. Total: KES {total_amount}", "success")

    # ✅ Redirect directly to receipt page
    return redirect(url_for("receipt", order_id=order_id))


@app.route("/cashier/receipt/<int:order_id>")
def receipt(order_id):
    db = get_db()

    order_row = db.execute("""
        SELECT co.id, co.patient_id, co.amount, co.status,
               p.name AS patient_name,
               p.medical_record_number,
               p.card_number
        FROM cashier_orders co
        JOIN patients p ON co.patient_id = p.id
        WHERE co.id=?
    """, (order_id,)).fetchone()

    if not order_row:
        flash("Receipt not found.", "danger")
        return redirect(url_for("cashier"))

    order = dict(order_row)

    # ✅ Use helper function
    totals = calculate_total_bill(order["patient_id"], db)

    return render_template(
        "receipt.html",
        order=order,
        ward_fee=totals["ward_total"],
        lab_total=totals["lab_total"],
        med_total=totals["med_total"],
        total_amount=totals["total_amount"]
    )



import csv
from io import StringIO

@app.route('/cashier/history')
def billing_history():
    db = get_db()
    orders = db.execute("""
        SELECT co.id, p.medical_record_number,
               p.first_name || ' ' || p.last_name AS patient_name,
               co.amount, co.created_at, co.status
        FROM cashier_orders co
        JOIN patients p ON co.patient_id = p.id
        WHERE co.status = 'paid'
        ORDER BY co.created_at DESC
    """).fetchall()

    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('billing_history.html', orders=orders, current_date=current_date)


@app.route('/cashier/history/pdf')
def export_billing_pdf():
    db = get_db()
    orders = db.execute("""
        SELECT co.id, p.medical_record_number,
               p.first_name || ' ' || p.last_name AS patient_name,
               co.amount, co.created_at, co.status
        FROM cashier_orders co
        JOIN patients p ON co.patient_id = p.id
        WHERE co.status = 'paid'
        ORDER BY co.created_at DESC
    """).fetchall()

    html = render_template('billing_history_pdf.html', orders=orders)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=billing_history.pdf'
    return response


@app.route('/cashier/history/csv')
def export_billing_csv():
    db = get_db()
    orders = db.execute("""
        SELECT co.id, p.medical_record_number,
               p.first_name || ' ' || p.last_name AS patient_name,
               co.amount, co.created_at, co.status
        FROM cashier_orders co
        JOIN patients p ON co.patient_id = p.id
        WHERE co.status = 'paid'
        ORDER BY co.created_at DESC
    """).fetchall()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Order ID', 'MRN', 'Patient', 'Amount', 'Paid At', 'Status'])
    for order in orders:
        cw.writerow([order['id'], order['medical_record_number'], order['patient_name'],
                     order['amount'], order['created_at'], order['status']])

    response = make_response(si.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=billing_history.csv'
    return response



def calculate_admission_total(patient_id, db):
    """
    Calculate the total admission cost for a patient.
    Combines ward fee, lab total, and medication total.
    """

    # Fetch the patient's current admission record
    admission_row = db.execute(
        "SELECT * FROM admissions WHERE patient_id=? AND status='admitted'",
        (patient_id,)
    ).fetchone()

    if not admission_row:
        return 0  # no active admission

    admission = dict(admission_row)

    ward_fee = calculate_ward_fee(admission, db)
    lab_total = calculate_lab_total(patient_id, db)
    med_total = calculate_medication_total(patient_id, db)

    return ward_fee + lab_total + med_total



def calculate_lab_total(patient_id, db):
    rows = db.execute("SELECT cost FROM lab_tests WHERE patient_id=?", (patient_id,)).fetchall()
    return sum(row["cost"] for row in rows)


def calculate_medication_total(patient_id, db):
    # Fetch prescriptions column for this patient
    row = db.execute("""
        SELECT prescriptions 
        FROM patient_medications 
        WHERE patient_id=?
    """, (patient_id,)).fetchone()

    if not row or not row[0]:
        return 0

    prescriptions = row[0]

    # Case 1: prescriptions is an integer (count)
    if isinstance(prescriptions, int):
        return prescriptions * 100

    # Case 2: prescriptions is a string (comma-separated names)
    if isinstance(prescriptions, str):
        items = [item.strip() for item in prescriptions.split(',') if item.strip()]
        total = 0
        for item in items:
            med_row = db.execute("SELECT price FROM medications WHERE name=?", (item,)).fetchone()
            if med_row:
                total += med_row['price']
        return total

    # Fallback if prescriptions is some other type
    return 0



def calculate_medication_total(prescriptions, db):
    # Guard against None or empty string
    if not prescriptions:
        return 0

    items = [item.strip() for item in prescriptions.split(',') if item.strip()]
    total = 0
    for item in items:
        row = db.execute("SELECT price FROM medications WHERE name=?", (item,)).fetchone()
        if row:
            total += row['price']
    return total


def calculate_lab_total(patient_id, db):
    rows = db.execute("""
        SELECT test_name FROM lab_orders WHERE patient_id=? AND status='fulfilled'
    """, (patient_id,)).fetchall()

    if not rows:  # Guard against None or empty list
        return 0

    total = 0
    for row in rows:
        if not row['test_name']:
            continue
        test = db.execute("SELECT price FROM lab_tests WHERE name=?", (row['test_name'],)).fetchone()
        if test:
            total += test['price']
    return total


def calculate_medication_total(patient_id, db):
    # Fetch prescriptions column for this patient
    row = db.execute("""
        SELECT prescriptions 
        FROM patient_medications 
        WHERE patient_id=?
    """, (patient_id,)).fetchone()

    if not row or not row[0]:
        return 0

    prescriptions = row[0]

    # Case 1: prescriptions is an integer (count of medications)
    if isinstance(prescriptions, int):
        return prescriptions * 100  # example cost logic

    # Case 2: prescriptions is a foreign key ID pointing to another table
    # (adjust this query if your schema is different)
    med_row = db.execute("""
        SELECT price 
        FROM medications 
        WHERE id=?
    """, (prescriptions,)).fetchone()

    if med_row:
        return med_row['price']

    # Fallback if prescriptions is some other type or not found
    return 0


def calculate_total_bill(patient_id, db):
    """
    Calculate the total bill for a patient by summing
    medicine, lab, and ward charges.
    """

    # --- Medicines ---
    med_total = db.execute("""
        SELECT COALESCE(SUM(p.quantity * m.unit_price), 0)
        FROM prescriptions p
        JOIN medicines m ON p.medicine_id = m.id
        WHERE p.patient_id=?
    """, (patient_id,)).fetchone()[0]

    # --- Lab Tests ---
    lab_total = db.execute("""
        SELECT COALESCE(SUM(l.test_price), 0)
        FROM lab_orders o
        JOIN lab_tests l ON o.test_id = l.id
        WHERE o.patient_id=?
    """, (patient_id,)).fetchone()[0]

    # --- Ward Charges ---
    ward_total = db.execute("""
        SELECT COALESCE(SUM(w.daily_rate * 
               (julianday(a.discharged_at) - julianday(a.admitted_at))), 0)
        FROM admissions a
        JOIN wards w ON a.ward = w.ward_name
        WHERE a.patient_id=?
          AND a.discharged_at IS NOT NULL
    """, (patient_id,)).fetchone()[0]

    # --- Total ---
    total_amount = med_total + lab_total + ward_total
    return {
        "med_total": med_total,
        "lab_total": lab_total,
        "ward_total": ward_total,
        "total_amount": total_amount
    }




@app.route('/doctor/prescribe/<int:patient_id>', methods=['GET', 'POST'])
def save_prescription(patient_id):
    db = get_db()
    if request.method == 'POST':
        selected_ids = request.form.getlist('medications')
        prescription_texts = []
        total_amount = 0

        for med_id in selected_ids:
            med = db.execute("SELECT * FROM medications WHERE id=?", (med_id,)).fetchone()
            if med:
                prescription_texts.append(f"{med['name']} {med['dosage']} - {med['instructions']}")
                total_amount += med['price']

        prescription_str = "; ".join(prescription_texts)

        # Save prescription
        db.execute("""
            INSERT INTO pharmacy_orders (patient_id, prescription, status, created_at)
            VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (patient_id, prescription_str))

        # Also create cashier order with bill
        db.execute("""
            INSERT INTO cashier_orders (patient_id, amount, status, created_at)
            VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (patient_id, total_amount))

        db.commit()
        flash('Prescription saved and sent to pharmacy & cashier.')
        return redirect(url_for('doctor'))

    # GET: show form
    medications = db.execute("SELECT * FROM medications").fetchall()
    patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    return render_template('prescription_template.html', patient=patient, medications=medications)


@app.route('/doctor/order/<int:patient_id>', methods=['GET', 'POST'])
def save_order(patient_id):
    db = get_db()
    if request.method == 'POST':
        med_ids = request.form.getlist('medications')
        lab_ids = request.form.getlist('lab_tests')
        adm_ids = request.form.getlist('admissions')

        prescription_texts = []
        total_amount = 0

        # Medications
        for med_id in med_ids:
            med = db.execute("SELECT * FROM medications WHERE id=?", (med_id,)).fetchone()
            if med:
                prescription_texts.append(f"{med['name']} {med['dosage']} - {med['instructions']}")
                total_amount += med['price']

        # Lab Tests
        for lab_id in lab_ids:
            test = db.execute("SELECT * FROM lab_tests WHERE id=?", (lab_id,)).fetchone()
            if test:
                prescription_texts.append(f"Lab Test: {test['name']}")
                total_amount += test['price']

        # Admissions
        for adm_id in adm_ids:
            adm = db.execute("SELECT * FROM admission_services WHERE id=?", (adm_id,)).fetchone()
            if adm:
                prescription_texts.append(f"Admission Service: {adm['service']}")
                total_amount += adm['price']

        prescription_str = "; ".join(prescription_texts)

        # Save pharmacy order
        db.execute("""
            INSERT INTO pharmacy_orders (patient_id, prescription, status, created_at)
            VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (patient_id, prescription_str))

        # Save cashier order
        db.execute("""
            INSERT INTO cashier_orders (patient_id, amount, status, created_at)
            VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (patient_id, total_amount))

        db.commit()
        flash(f'Order saved. Total bill: KES {total_amount}')
        return redirect(url_for('doctor'))

    # GET: show form
    medications = db.execute("SELECT * FROM medications").fetchall()
    lab_tests = db.execute("SELECT * FROM lab_tests").fetchall()
    admissions = db.execute("SELECT * FROM admission_services").fetchall()
    patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    return render_template('prescription_template.html',
                           patient=patient,
                           medications=medications,
                           lab_tests=lab_tests,
                           admissions=admissions)


# ---------------- Patient List ----------------

@app.route('/patients')
def patients():
    db = get_db()
    q = request.args.get('q', '').strip()

    if q:
        patients = db.execute("""
            SELECT * FROM patients
            WHERE is_active = 1
              AND (first_name LIKE ? OR last_name LIKE ? OR medical_record_number LIKE ?)
            ORDER BY created_at DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        patients = db.execute("""
            SELECT * FROM patients
            WHERE is_active = 1
            ORDER BY created_at DESC
        """).fetchall()

    return render_template('patients.html', patients=patients)


@app.route('/patients/<int:id>')
def patient_detail(id):
    db = get_db()

    # Patient record
    patient = db.execute("SELECT * FROM patients WHERE id=?", (id,)).fetchone()
    if not patient:
        abort(404)

    # Medical history
    history = db.execute("""
        SELECT diagnosis, symptoms, created_at
        FROM medical_history
        WHERE patient_id=?
        ORDER BY created_at DESC
    """, (id,)).fetchall()

    # Last medication
    last_med = db.execute("""
        SELECT prescription, created_at
        FROM pharmacy_orders
        WHERE patient_id=?
        ORDER BY created_at DESC
        LIMIT 1
    """, (id,)).fetchone()

    return render_template(
        'patient_detail.html',
        patient=patient,
        history=history,
        last_med=last_med
    )



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

if __name__ == "__main__":
    app.run(debug=True, port=5002)




# @app.route('/cashier/mark_paid', methods=['POST'])
# def mark_paid():
#     order_id = request.form['order_id']
#     db = get_db()

#     patient = db.execute("""
#         SELECT p.*, co.amount
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.id=?
#     """, (order_id,)).fetchone()

#     # Mark order as paid
#     db.execute("UPDATE cashier_orders SET status='paid' WHERE id=?", (order_id,))
#     db.execute("""
#         UPDATE patients SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?
#     """, (patient['id'],))
#     db.commit()

#     flash('Payment recorded successfully. Receipt generated.', 'success')
#     return render_template('receipt.html', patient=patient, amount=patient['amount'])


# @app.route('/cashier')
# def cashier():
#     db = get_db()
#     orders = db.execute("""
#         SELECT co.id, p.medical_record_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                co.amount, co.created_at, co.status
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.status = 'pending'
#         ORDER BY co.created_at ASC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('cashier.html', orders=orders, current_date=current_date)



# @app.route('/cashier/mark_paid', methods=['POST'])
# def mark_paid():
#     order_id = request.form['order_id']
#     db = get_db()

#     patient_id = db.execute("SELECT patient_id FROM cashier_orders WHERE id=?", (order_id,)).fetchone()['patient_id']

#     db.execute("UPDATE cashier_orders SET status='paid' WHERE id=?", (order_id,))
#     db.execute("""
#         UPDATE patients SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?
#     """, (patient_id,))
#     db.commit()

#     flash('Payment recorded successfully. Patient completed.')
#     return redirect(url_for('cashier'))

# @app.route('/cashier/mark_paid', methods=['POST'])
# def mark_paid():
#     order_id = request.form['order_id']
#     db = get_db()
#     db.execute("""
#         UPDATE cashier_orders
#         SET status = 'paid'
#         WHERE id = ?
#     """, (order_id,))
#     db.commit()
#     flash('Payment recorded successfully.')
#     return redirect(url_for('cashier'))


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


# @app.route('/patient/<int:id>')
# def patient_detail(id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
#     db.close()

#     if not patient:
#         flash("Patient not found.", "danger")
#         return redirect(url_for('checkin'))

#     return render_template('patient_detail.html', patient=patient)


# billing history.....................

# @app.route('/cashier/history')
# def billing_history():
#     db = get_db()
#     orders = db.execute("""
#         SELECT co.id, p.medical_record_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                co.amount, co.created_at, co.status
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.status = 'paid'
#         ORDER BY co.created_at DESC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('billing_history.html', orders=orders, current_date=current_date)

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
#             flash(f"No patient found with card number: {card_number}. Please register.", 'warning')
#             return redirect(url_for('register'))

#     return render_template('checkin.html', generated_mrn=generated_mrn)


# @app.route('/send_to_lab/<int:patient_id>', methods=['POST'])
# def send_to_lab(patient_id):
#     test_name = request.form.get('test_name', 'General Test')
#     db = get_db()
#     db.execute("""
#         INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at)
#         VALUES (?, ?, ?, CURRENT_TIMESTAMP)
#     """, (patient_id, test_name, 'Dr. Wanyama'))
#     db.commit()
#     flash('Lab test ordered successfully')
#     return redirect(url_for('doctor'))


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

# def order_lab_test():
#     patient_id = request.form['patient_id']
#     test_name = request.form['test_name']
#     db = get_db()
#     db.execute("INSERT INTO lab_orders (patient_id, test_name, ordered_by) VALUES (?, ?, ?)",
#                (patient_id, test_name, 'Dr. Wanyama'))
#     db.commit()
#     flash('Lab test ordered successfully')
#     return redirect(url_for('doctor'))



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









# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# import sqlite3
# from datetime import datetime
# import africastalking
# from flask import make_response
# from weasyprint import HTML
# from flask_login import LoginManager
# from flask_login import login_required
# from werkzeug.security import check_password_hash
# from flask_login import LoginManager


# import africastalking

# import sqlite3
# from flask import g, Flask

# # app = Flask(__name__)

# from flask import Flask
# import os, secrets

# app = Flask(__name__)

# # Use a secure random key. In production, load from environment.
# app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
# DATABASE = "your_database.db"   # replace with your actual DB file path

# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(
#             DATABASE,
#             detect_types=sqlite3.PARSE_DECLTYPES,
#             check_same_thread=False,   # allows multi-threaded use
#             timeout=10                 # waits up to 10s if locked
#         )
#         g.db.row_factory = sqlite3.Row
#     return g.db

# @app.teardown_appcontext
# def close_connection(exception):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()




# # # Sandbox credentials
# # username = "sandbox"
# # api_key = "YOUR_SANDBOX_API_KEY"

# # # Manually initialize only SMS service
# # sms = africastalking.SMS
# # sms.username = username
# # sms.api_key = api_key









# # app = Flask(__name__)  # Your existing app setup

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'  # This should match your login route name




# # Initialize Africa's Talking SDK
# import africastalking

# # username = "sandbox"  # or your live username
# # api_key = "your_actual_api_key"

# # africastalking.initialize(username, api_key)
# # sms = africastalking.SMS
# # sms.send("New prescription for Patient XYZ", ["+254711732324"])

# # africastalking.initialize(username="your_username", api_key="your_api_key")
# # sms = africastalking.SMS
# # sms.send("New prescription for Patient XYZ", ["+254711732324"])

# login_manager.login_view = 'login'


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         db = get_db()
#         user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

#         if user and check_password_hash(user['password'], password):
#             login_user(User(user))  # wrap in your User class
#             flash('Logged in successfully!')
#             return redirect(url_for('dashboard'))  # or wherever you want to land
#         else:
#             flash('Invalid credentials')

#     return render_template('login.html')


# # @login_manager.user_loader
# def load_user(user_id):
#     db = get_db()
#     user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
#     return User(user) if user else None


# login_manager.login_view = 'user_login'

# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('Logged out successfully!')
#     return redirect(url_for('login'))

# from flask import Flask
# import os, secrets

# app = Flask(__name__)

# # Use a secure random key. In production, load from environment.
# app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

# # ---------------- Database Connection ----------------
# def get_db():
#     conn = sqlite3.connect('hospital.db')
#     conn.row_factory = sqlite3.Row
#     return conn

# # login_manager = LoginManager()
# # login_manager.init_app(app)
# # login_manager.login_view = 'login'  # or whatever your login route is


# @login_manager.user_loader
# def load_user(user_id):
#     db = get_db()
#     user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
#     return User(user) if user else None  # Wrap in your User class


# @login_manager.user_loader
# def load_user(user_id):
#     db = get_db()
#     return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

# class User:
#     def __init__(self, row):
#         self.id = row['id']
#         self.username = row['username']
#         self.role = row['role']

#     @property
#     def is_authenticated(self):
#         return True

#     @property
#     def is_active(self):
#         return True

#     @property
#     def is_anonymous(self):
#         return False

#     def get_id(self):
#         return str(self.id)


# # ---------------- Dashboard ----------------
# import os
# from flask import Flask, render_template, request
# from datetime import datetime

# app = Flask(__name__)

# def get_stats(period, db):
#     today_sql = datetime.now().strftime('%Y-%m-%d')

#     if period == 'week':
#         query_range = "DATE(appointment_date) >= date('now','-7 day')"
#     elif period == 'quarter':
#         query_range = "DATE(appointment_date) >= date('now','-90 day')"
#     elif period == 'year':
#         query_range = "DATE(appointment_date) >= date('now','-365 day')"
#     else:  # default month
#         query_range = "DATE(appointment_date) >= date('now','start of month')"

#     stats = {
#         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
#         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
#         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
#         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled','confirmed')").fetchone()[0],
#         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status='completed'", (today_sql,)).fetchone()[0],
#         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status='admitted'").fetchone()[0],
#         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status='active'").fetchone()[0],
#         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status='available'").fetchone()[0],
#         'efficiency': 0
#     }

#     if stats['today_appointments'] > 0:
#         stats['efficiency'] = round((stats['completed_appointments_today'] / stats['today_appointments']) * 100, 2)

#     return stats

# def get_appointments(period, db):
#     today_sql = datetime.now().strftime('%Y-%m-%d')
#     return db.execute("""
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

# def get_queue(period, db):
#     today_sql = datetime.now().strftime('%Y-%m-%d')
#     return db.execute("""
#         SELECT a.id, p.first_name || ' ' || p.last_name AS patient_name, a.status
#         FROM appointments a
#         JOIN patients p ON a.patient_id = p.id
#         WHERE DATE(a.appointment_date) = ? AND a.status IN ('scheduled','confirmed')
#         ORDER BY a.appointment_date ASC
#     """, (today_sql,)).fetchall()

# @app.route('/')
# @app.route('/dashboard')
# def dashboard():
#     use_dummy = os.environ.get("USE_DUMMY_DATA", "false").lower() == "true"
#     period = request.args.get('period', 'month')
#     today_display = datetime.now().strftime('%A, %B %d, %Y')

#     if use_dummy:
#         stats = {
#             'total_patients': 120,
#             'total_doctors': 15,
#             'today_appointments': 8,
#             'pending_appointments': 3,
#             'completed_appointments_today': 5,
#             'efficiency': 83,
#             'available_beds': 12,
#             'in_labor': 2
#         }
#         appointments = [
#             {'patient_name': 'Jane Doe', 'doctor_name': 'Dr. Otieno', 'time': '10:00 AM'},
#             {'patient_name': 'John Mwangi', 'doctor_name': 'Dr. Achieng', 'time': '11:30 AM'}
#         ]
#         queue = []
#     else:
#         db = get_db()
#         stats = get_stats(period, db)
#         appointments = get_appointments(period, db)
#         queue = get_queue(period, db)

#     return render_template(
#         'dashboard.html',
#         stats=stats,
#         appointments=appointments,
#         queue=queue,
#         current_date=today_display,
#         period=period
#     )


# # @app.route('/')
# # def dashboard():
# #     db = get_db()
# #     today_sql = datetime.now().strftime('%Y-%m-%d')
# #     today_display = datetime.now().strftime('%A, %B %d, %Y')

# #     stats = {
# #         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
# #         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
# #         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
# #         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
# #         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today_sql,)).fetchone()[0],
# #         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
# #         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
# #         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
# #         'efficiency': 0
# #     }

# #     queue = db.execute("""
# #     SELECT a.id, p.first_name || ' ' || p.last_name AS patient_name, a.status
# #     FROM appointments a
# #     JOIN patients p ON a.patient_id = p.id
# #     WHERE DATE(a.appointment_date) = ? AND a.status IN ('scheduled', 'confirmed')
# #     ORDER BY a.appointment_date ASC
# # """, (today_sql,)).fetchall()


# #     if stats['today_appointments'] > 0:
# #         stats['efficiency'] = round((stats['completed_appointments_today'] / stats['today_appointments']) * 100, 2)

# #     appointments = db.execute("""
# #         SELECT a.*, 
# #                p.first_name || ' ' || p.last_name AS patient_name,
# #                d.first_name || ' ' || d.last_name AS doctor_name,
# #                strftime('%H:%M', a.appointment_date) AS time
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         JOIN doctors d ON a.doctor_id = d.id
# #         WHERE DATE(a.appointment_date) = ?
# #         ORDER BY a.appointment_date ASC
# #     """, (today_sql,)).fetchall()

# #     return render_template('dashboard.html', stats=stats, appointments=appointments, current_date=today_display)


# # @app.route('/dashboard')
# # def dashboard_view():
# #     stats = {
# #         'total_patients': 120,
# #         'total_doctors': 15,
# #         'today_appointments': 8,
# #         'pending_appointments': 3,
# #         'completed_appointments_today': 5,
# #         'efficiency': 83,
# #         'available_beds': 12,
# #         'in_labor': 2
# #     }

# #     stats_grid = [
# #         {'title': 'Total Patients', 'value': stats['total_patients']},
# #         {'title': 'Active Doctors', 'value': stats['total_doctors']},
# #         {'title': "Today's Appointments", 'value': stats['today_appointments']},
# #         {'title': 'Pending Appointments', 'value': stats['pending_appointments']},
# #         {'title': 'Admitted Patients', 'value': 18},
# #         {'title': 'In Labor', 'value': stats['in_labor']}
# #     ]

# #     appointments = [
# #         {'patient_name': 'Jane Doe', 'doctor_name': 'Dr. Otieno', 'time': '10:00 AM'},
# #         {'patient_name': 'John Mwangi', 'doctor_name': 'Dr. Achieng', 'time': '11:30 AM'}
# #     ]

# #     return render_template('dashboard.html', stats=stats, stats_grid=stats_grid, appointments=appointments, current_date='September 10, 2025')





# # def get_stats(period, db):
# #     """Fetch stats based on the selected period."""
# #     today_sql = datetime.now().strftime('%Y-%m-%d')

# #     if period == 'week':
# #         # Example: last 7 days
# #         query_range = "DATE(appointment_date) >= date('now','-7 day')"
# #     elif period == 'quarter':
# #         # Example: last 90 days
# #         query_range = "DATE(appointment_date) >= date('now','-90 day')"
# #     elif period == 'year':
# #         # Example: last 365 days
# #         query_range = "DATE(appointment_date) >= date('now','-365 day')"
# #     else:  # default month
# #         query_range = "DATE(appointment_date) >= date('now','start of month')"

# #     stats = {
# #         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
# #         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
# #         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
# #         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled','confirmed')").fetchone()[0],
# #         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status='completed'", (today_sql,)).fetchone()[0],
# #         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status='admitted'").fetchone()[0],
# #         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status='active'").fetchone()[0],
# #         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status='available'").fetchone()[0],
# #         'efficiency': 0
# #     }

# #     if stats['today_appointments'] > 0:
# #         stats['efficiency'] = round((stats['completed_appointments_today'] / stats['today_appointments']) * 100, 2)

# #     return stats

# # def get_appointments(period, db):
# #     today_sql = datetime.now().strftime('%Y-%m-%d')
# #     return db.execute("""
# #         SELECT a.*, 
# #                p.first_name || ' ' || p.last_name AS patient_name,
# #                d.first_name || ' ' || d.last_name AS doctor_name,
# #                strftime('%H:%M', a.appointment_date) AS time
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         JOIN doctors d ON a.doctor_id = d.id
# #         WHERE DATE(a.appointment_date) = ?
# #         ORDER BY a.appointment_date ASC
# #     """, (today_sql,)).fetchall()

# # def get_queue(period, db):
# #     today_sql = datetime.now().strftime('%Y-%m-%d')
# #     return db.execute("""
# #         SELECT a.id, p.first_name || ' ' || p.last_name AS patient_name, a.status
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         WHERE DATE(a.appointment_date) = ? AND a.status IN ('scheduled','confirmed')
# #         ORDER BY a.appointment_date ASC
# #     """, (today_sql,)).fetchall()

# # @app.route('/')
# # @app.route('/dashboard')
# # def dashboard():
# #     db = get_db()
# #     period = request.args.get('period', 'month')  # default to month
# #     today_display = datetime.now().strftime('%A, %B %d, %Y')

# #     stats = get_stats(period, db)
# #     appointments = get_appointments(period, db)
# #     queue = get_queue(period, db)

# #     return render_template(
# #         'dashboard.html',
# #         stats=stats,
# #         appointments=appointments,
# #         queue=queue,
# #         current_date=today_display,
# #         period=period
# #     )

# # from flask import Flask, render_template, request
# # from datetime import datetime

# # app = Flask(__name__)

# # @app.route('/')
# # @app.route('/dashboard')
# # def dashboard():
# #     period = request.args.get('period', 'month')  # default to month

# #     db = get_db()
# #     today_sql = datetime.now().strftime('%Y-%m-%d')
# #     today_display = datetime.now().strftime('%A, %B %d, %Y')

# #     # Example: adjust queries based on period
# #     if period == 'week':
# #         # fetch stats for the week
# #         stats = get_stats_for_week(db)
# #     elif period == 'quarter':
# #         stats = get_stats_for_quarter(db)
# #     elif period == 'year':
# #         stats = get_stats_for_year(db)
# #     else:  # default month
# #         stats = get_stats_for_month(db)

# #     appointments = get_appointments(period)
# #     queue = get_queue(period)

# #     return render_template(
# #         'dashboard.html',
# #         stats=stats,
# #         appointments=appointments,
# #         queue=queue,
# #         current_date=today_display,
# #         period=period
# #     )



# @app.route('/release/<int:patient_id>')
# def release_summary(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     treatments = db.execute("SELECT * FROM treatments WHERE patient_id = ?", (patient_id,)).fetchall()
#     labs = db.execute("SELECT * FROM lab_results WHERE patient_id = ?", (patient_id,)).fetchall()
#     prescriptions = db.execute("SELECT * FROM pharmacy_orders WHERE patient_id = ?", (patient_id,)).fetchall()
#     billing = db.execute("SELECT SUM(amount) FROM billing WHERE patient_id = ?", (patient_id,)).fetchone()[0]

#     return render_template('release.html', patient=patient, treatments=treatments, labs=labs, prescriptions=prescriptions, billing=billing)





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
#             # Get last visit date
#             last_visit = db.execute("""
#                 SELECT MAX(appointment_date) AS last_visit
#                 FROM appointments
#                 WHERE patient_id = ?
#             """, (patient['id'],)).fetchone()

#             # Get last prescription
#             last_prescription = db.execute("""
#                 SELECT prescriptions, updated_at
#                 FROM patients
#                 WHERE id = ?
#             """, (patient['id'],)).fetchone()

#             # Queue patient if not already queued today
#             existing_appt = db.execute("""
#                 SELECT id FROM appointments 
#                 WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
#             """, (patient['id'],)).fetchone()

#             if not existing_appt:
#                 db.execute("""
#                     INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
#                     VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
#                 """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic

#                 # ✅ Update patient status so doctor sees them
#                 db.execute("""
#                     UPDATE patients SET status='scheduled', updated_at=CURRENT_TIMESTAMP WHERE id=?
#                 """, (patient['id'],))

#                 db.commit()

#             return render_template(
#                 'checkin_details.html',
#                 patient=patient,
#                 last_visit=last_visit['last_visit'] if last_visit else None,
#                 last_prescription=last_prescription['prescriptions'] if last_prescription else None,
#                 generated_mrn=generated_mrn
#             )
#         else:
#             flash(f"No patient found with card number: {card_number}. Please register.", 'warning')
#             return redirect(url_for('register'))

#     return render_template('checkin.html', generated_mrn=generated_mrn)


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

#         # Generate card number automatically
#         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
#         next_id = (last or 0) + 1
#         card_number = f"HCO{next_id:05d}"
#         mrn = f"MRN{next_id:05d}"

#         full_name = f"{data['first_name']} {data['last_name']}"

#         cursor = db.execute("""
#             INSERT INTO patients (
#                 medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
#                 status, is_active, created_at, updated_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#         """, (
#             mrn,
#             card_number,
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
#         """, (new_id, 1))
#         db.commit()

#         flash(f'Patient registered successfully! Card Number: {card_number}', 'success')
#         return redirect(url_for('print_card', patient_id=new_id))

#     generated_mrn = f"MRN{int(time.time())}"
#     return render_template('register.html', generated_mrn=generated_mrn)


# @app.route('/print_card/<int:patient_id>')
# def print_card(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     if not patient:
#         flash("Patient not found.", "danger")
#         return redirect(url_for('register'))

#     # Render the patient card template
#     return render_template('patient_card.html', patient=patient)

# # @app.route('/print_card/<int:patient_id>')
# # def print_card(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
# #     flash('Card printed successfully. Patient sent to doctor queue.', 'success')
# #     # ✅ After printing, go back to doctor dashboard
# #     return redirect(url_for('doctor'))




# # ---------------- Doctor Interface ----------------
# # ---------------- DOCTOR ----------------
# # @app.route('/doctor', methods=['GET', 'POST'])
# # def doctor():
# #     db = get_db()

# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
# #         prescriptions = request.form['prescriptions']
# #         billing_amount = request.form['billing_amount']

# #         db.execute("""
# #             UPDATE patients 
# #             SET symptoms = ?, diagnosis = ?, prescriptions = ?, status = 'completed', billing_amount = ?, updated_at = CURRENT_TIMESTAMP 
# #             WHERE id = ?
# #         """, (symptoms, diagnosis, prescriptions, billing_amount, patient_id))

# #         db.execute("""
# #             INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by, created_at, status)
# #             VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
# #         """, (patient_id, prescriptions, 'Dr. Wanyama'))

# #         db.execute("""
# #             INSERT INTO cashier_orders (patient_id, amount, status)
# #             VALUES (?, ?, 'pending')
# #         """, (patient_id, billing_amount))

# #         db.commit()
# #         flash('Prescription saved, patient sent to pharmacy and cashier!')
# #         return redirect(url_for('doctor_dashboard'))

# #     patients = db.execute("""
# #         SELECT id AS patient_id, first_name || ' ' || last_name AS name, status
# #         FROM patients
# #         WHERE status IN ('scheduled', 'awaiting_doctor')
# #         ORDER BY updated_at ASC
# #     """).fetchall()

# #     current_date = datetime.now().strftime('%A, %B %d, %Y')
# #     return render_template('doctor.html', patients=patients, current_date=current_date)

# @app.route('/doctor/<int:patient_id>', methods=['GET'])
# def doctor_interface(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
#     medications = db.execute("SELECT * FROM medications").fetchall()
#     lab_tests = db.execute("SELECT * FROM lab_tests").fetchall()
#     admissions = db.execute("SELECT * FROM admissions").fetchall()

#     return render_template(
#         'doctor.html',
#         patient=patient,
#         medications=medications,
#         lab_tests=lab_tests,
#         admissions=admissions,
#         current_date=datetime.now().strftime("%Y-%m-%d %H:%M")
#     )


# @app.route('/doctor', methods=['GET', 'POST'])
# def doctor():
#     db = get_db()

#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         symptoms = request.form['symptoms']
#         diagnosis = request.form['diagnosis']
#         prescriptions = request.form['prescriptions']
#         billing_amount = request.form['billing_amount']

#         # Update patient status to awaiting_pharmacy
#         db.execute("""
#             UPDATE patients 
#             SET symptoms=?, diagnosis=?, prescriptions=?, status='awaiting_pharmacy',
#                 billing_amount=?, updated_at=CURRENT_TIMESTAMP
#             WHERE id=?
#         """, (symptoms, diagnosis, prescriptions, billing_amount, patient_id))

#         # Insert pharmacy order
#         db.execute("""
#             INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by, created_at, status)
#             VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
#         """, (patient_id, prescriptions, 'Dr. Wanyama'))

#         # Insert cashier order
#         db.execute("""
#             INSERT INTO cashier_orders (patient_id, amount, status)
#             VALUES (?, ?, 'pending')
#         """, (patient_id, billing_amount))

#         db.commit()
#         flash('Prescription saved, patient sent to pharmacy and cashier!')
#         return redirect(url_for('doctor'))

#     patients = db.execute("""
#         SELECT id AS patient_id, first_name || ' ' || last_name AS name, status
#         FROM patients
#         WHERE status IN ('scheduled', 'awaiting_doctor')
#         ORDER BY updated_at ASC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('doctor.html', patients=patients, current_date=current_date)



# @app.route('/doctor/<int:patient_id>')
# def doctor_detail(patient_id):
#     db = get_db()
#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     return render_template('doctor.html', patient=patient, current_date=current_date)





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
# @app.route('/lab/order', methods=['GET', 'POST'])
# def order_lab_test():
#     db = get_db()
#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         test_name = request.form['test_name']
#     else:  # GET request
#         patient_id = request.args.get('patient_id')
#         test_name = request.args.get('test_name', 'General Test')

#     db.execute("""
#         INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at)
#         VALUES (?, ?, ?, CURRENT_TIMESTAMP)
#     """, (patient_id, test_name, 'Dr. Wanyama'))
#     db.commit()
#     flash('Lab test ordered successfully')
#     return redirect(url_for('doctor'))




# @app.route('/doctor/<int:patient_id>')
# def doctor_dashboard(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
#     return render_template('doctor.html', patient=patient)


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


# # Doctor sends patient to pharmacy
# @app.route('/send_to_pharmacy/<int:patient_id>')
# def send_to_pharmacy(patient_id):
#     db = get_db()
#     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

#     db.execute("""
#         INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by, created_at, status)
#         VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
#     """, (patient_id, patient['prescriptions'], 'Dr. Wanyama'))
#     db.commit()

#     flash(f"Patient {patient['first_name']} {patient['last_name']} sent to pharmacy.", 'success')
#     return redirect(url_for('doctor'))


# # Pharmacy dashboard
# # ---------------- PHARMACY ----------------
# @app.route('/pharmacy')
# def pharmacy():
#     db = get_db()
#     orders = db.execute("""
#         SELECT po.id, p.medical_record_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                po.prescription, po.ordered_by, po.created_at,
#                po.status, po.fulfilled_by, po.fulfilled_at
#         FROM pharmacy_orders po
#         JOIN patients p ON po.patient_id = p.id
#         ORDER BY po.created_at DESC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('pharmacy.html', orders=orders, current_date=current_date)



# @app.route('/pharmacy/fulfill', methods=['POST'])
# def fulfill_order():
#     order_id = request.form['order_id']
#     db = get_db()

#     order = db.execute("""
#         SELECT po.patient_id, po.prescription
#         FROM pharmacy_orders po
#         WHERE po.id=?
#     """, (order_id,)).fetchone()

#     # Mark pharmacy order as fulfilled
#     db.execute("""
#         UPDATE pharmacy_orders
#         SET status='fulfilled', fulfilled_by='Pharmacist A', fulfilled_at=CURRENT_TIMESTAMP
#         WHERE id=?
#     """, (order_id,))

#     # ✅ Calculate totals
#     med_total = calculate_medication_total(order['prescription'], db)
#     lab_total = calculate_lab_total(order['patient_id'], db)
#     admission_total = calculate_admission_total(order['patient_id'], db)

#     bill_amount = med_total + lab_total + admission_total

#     # Insert cashier order
#     db.execute("""
#         INSERT INTO cashier_orders (patient_id, amount, status, created_at)
#         VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
#     """, (order['patient_id'], bill_amount))

#     db.commit()
#     flash(f'Order fulfilled and sent to cashier. Bill: KES {bill_amount}')
#     return redirect(url_for('pharmacy'))



# # Doctor sends patient to lab

# @app.route('/send_to_lab/<int:patient_id>', methods=['POST'])
# def send_to_lab(patient_id):
#     test_name = request.form.get('test_name', 'General Test')
#     db = get_db()
#     db.execute("""
#         INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at, status)
#         VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
#     """, (patient_id, test_name, 'Dr. Wanyama'))

#     # Update patient status
#     db.execute("""
#         UPDATE patients SET status='awaiting_lab', updated_at=CURRENT_TIMESTAMP WHERE id=?
#     """, (patient_id,))
#     db.commit()

#     flash('Lab test ordered successfully')
#     return redirect(url_for('doctor'))

# # @app.route('/send_to_lab/<int:patient_id>', methods=['POST'])
# # def send_to_lab(patient_id):
# #     test_name = request.form.get('test_name', 'General Test')
# #     db = get_db()
# #     db.execute("""
# #         INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at, status)
# #         VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
# #     """, (patient_id, test_name, 'Dr. Wanyama'))
# #     db.commit()
# #     flash('Lab test ordered successfully')
# #     return redirect(url_for('doctor'))




# # Lab dashboard
# @app.route('/lab', methods=['GET'])
# def lab():
#     db = get_db()
#     orders = db.execute("""
#         SELECT lo.id, p.medical_record_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                lo.test_name, lo.ordered_by, lo.created_at, lo.status
#         FROM lab_orders lo
#         JOIN patients p ON lo.patient_id = p.id
#         WHERE lo.status = 'pending'
#         ORDER BY lo.created_at DESC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('lab.html', orders=orders, current_date=current_date)


# @app.route('/lab/fulfill', methods=['POST'])
# def fulfill_lab_order():
#     order_id = request.form['order_id']
#     lab_results = request.form['lab_results']
#     db = get_db()

#     patient_id = db.execute("SELECT patient_id FROM lab_orders WHERE id=?", (order_id,)).fetchone()['patient_id']

#     # Save results and send back to doctor
#     db.execute("""
#         UPDATE patients
#         SET lab_results=?, status='awaiting_doctor', updated_at=CURRENT_TIMESTAMP
#         WHERE id=?
#     """, (lab_results, patient_id))

#     db.execute("""
#         UPDATE lab_orders
#         SET status='fulfilled', fulfilled_at=CURRENT_TIMESTAMP
#         WHERE id=?
#     """, (order_id,))
#     db.commit()

#     flash('Lab results saved and patient sent back to doctor.')
#     return redirect(url_for('lab'))



# # ---------------- Labor & Delivery Dashboard ----------------
# @app.route('/labor_delivery')
# def labor_delivery_dashboard():
#     db = get_db()
#     records = db.execute('SELECT * FROM labor_records WHERE status="active"').fetchall()
#     delivered_today = db.execute('SELECT COUNT(*) FROM labor_records WHERE status="delivered" AND DATE(delivery_time)=DATE("now")').fetchone()[0]
#     avg_labor = db.execute('SELECT AVG(duration) FROM labor_records WHERE duration IS NOT NULL').fetchone()[0] or 0

#     metrics = {
#         'in_labor': len(records),
#         'delivered_today': delivered_today,
#         'maternity_beds': db.execute("SELECT COUNT(*) FROM beds WHERE ward = 'maternity'").fetchone()[0],
#         'avg_labor': round(avg_labor, 1)
#     }

#     return render_template('labor_delivery.html', metrics=metrics, records=records)

# # ---------------- Start Labor Record ----------------
# @app.route('/labor_delivery/start', methods=['POST'])
# def start_labor_record():
#     db = get_db()
#     patient_name = request.form['patient_name']
#     db.execute('INSERT INTO labor_records (patient_name, start_time, status) VALUES (?, ?, ?)',
#                (patient_name, datetime.now(), 'active'))
#     db.commit()
#     flash('Labor record started successfully!')
#     return redirect(url_for('labor_delivery_dashboard'))

# # ---------------- Complete Labor Record ----------------
# @app.route('/labor_delivery/complete', methods=['POST'])
# def complete_labor_record():
#     record_id = request.form['record_id']
#     db = get_db()
#     record = db.execute("SELECT start_time FROM labor_records WHERE id = ?", (record_id,)).fetchone()

#     if record:
#         start_time = datetime.fromisoformat(record['start_time'])
#         delivery_time = datetime.now()
#         duration = round((delivery_time - start_time).total_seconds() / 3600, 2)

#         db.execute("""
#             UPDATE labor_records
#             SET delivery_time = ?, duration = ?, status = 'delivered'
#             WHERE id = ?
#         """, (delivery_time, duration, record_id))
#         db.commit()
#         flash('Labor marked as delivered successfully!')

#     return redirect(url_for('labor_delivery_dashboard'))


# # from flask import Flask, render_template, request, redirect, url_for
# # from datetime import datetime

# # app = Flask(__name__)

# @app.route('/admission', methods=['GET', 'POST'])
# def admission():
#     db = get_db()

#     if request.method == 'POST':
#         patient_id = request.form['patient_id']
#         ward = request.form['ward']
#         bed_number = request.form['bed_number']
#         reason = request.form['reason']
#         admitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#         # Insert admission record
#         db.execute("""
#             INSERT INTO admissions (patient_id, ward, bed_number, reason, admitted_at, status)
#             VALUES (?, ?, ?, ?, ?, ?)
#         """, (patient_id, ward, bed_number, reason, admitted_at, 'admitted'))
#         db.commit()

#         # Update patient admission_status
#         db.execute("UPDATE patients SET admission_status = 'admitted' WHERE id = ?", (patient_id,))
#         db.commit()

#         # Update bed status
#         db.execute("UPDATE beds SET status = 'occupied' WHERE bed_number = ?", (bed_number,))
#         db.commit()

#         return redirect(url_for('admission'))

#     # Fetch current admissions
#     admissions = db.execute("""
#         SELECT a.id, p.first_name || ' ' || p.last_name AS patient_name,
#                a.ward, a.bed_number, a.reason, a.admitted_at, a.status
#         FROM admissions a
#         JOIN patients p ON a.patient_id = p.id
#         WHERE a.status = 'admitted'
#         ORDER BY a.admitted_at DESC
#     """).fetchall()

#     return render_template('admission.html', admissions=admissions)


# # ---------------- Billing ----------------
# # ---------------- CASHIER ----------------
# @app.route('/cashier')
# def cashier():
#     db = get_db()
#     # Show all pending cashier orders
#     orders = db.execute("""
#         SELECT co.id, p.medical_record_number, p.card_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                co.amount, co.created_at, co.status
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.status = 'pending'
#         ORDER BY co.created_at ASC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('cashier.html', orders=orders, current_date=current_date)


# @app.route('/cashier/mark_paid', methods=['POST'])
# def mark_paid():
#     order_id = request.form['order_id']
#     db = get_db()

#     patient = db.execute("""
#         SELECT p.*, co.amount
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.id=?
#     """, (order_id,)).fetchone()

#     # Example: calculate breakdown (replace with your actual functions)
#     med_total = calculate_medication_total(patient['prescriptions'], db)
#     lab_total = calculate_lab_total(patient['id'], db)
#     admission_total = calculate_admission_total(patient['id'], db)

#     db.execute("UPDATE cashier_orders SET status='paid' WHERE id=?", (order_id,))
#     db.execute("""
#         UPDATE patients SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?
#     """, (patient['id'],))
#     db.commit()

#     return render_template(
#         'receipt.html',
#         patient=patient,
#         med_total=med_total,
#         lab_total=lab_total,
#         admission_total=admission_total,
#         amount=patient['amount']
#     )

# import csv
# from io import StringIO

# @app.route('/cashier/history')
# def billing_history():
#     db = get_db()
#     orders = db.execute("""
#         SELECT co.id, p.medical_record_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                co.amount, co.created_at, co.status
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.status = 'paid'
#         ORDER BY co.created_at DESC
#     """).fetchall()

#     current_date = datetime.now().strftime('%A, %B %d, %Y')
#     return render_template('billing_history.html', orders=orders, current_date=current_date)


# @app.route('/cashier/history/pdf')
# def export_billing_pdf():
#     db = get_db()
#     orders = db.execute("""
#         SELECT co.id, p.medical_record_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                co.amount, co.created_at, co.status
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.status = 'paid'
#         ORDER BY co.created_at DESC
#     """).fetchall()

#     html = render_template('billing_history_pdf.html', orders=orders)
#     pdf = HTML(string=html).write_pdf()
#     response = make_response(pdf)
#     response.headers['Content-Type'] = 'application/pdf'
#     response.headers['Content-Disposition'] = 'attachment; filename=billing_history.pdf'
#     return response


# @app.route('/cashier/history/csv')
# def export_billing_csv():
#     db = get_db()
#     orders = db.execute("""
#         SELECT co.id, p.medical_record_number,
#                p.first_name || ' ' || p.last_name AS patient_name,
#                co.amount, co.created_at, co.status
#         FROM cashier_orders co
#         JOIN patients p ON co.patient_id = p.id
#         WHERE co.status = 'paid'
#         ORDER BY co.created_at DESC
#     """).fetchall()

#     si = StringIO()
#     cw = csv.writer(si)
#     cw.writerow(['Order ID', 'MRN', 'Patient', 'Amount', 'Paid At', 'Status'])
#     for order in orders:
#         cw.writerow([order['id'], order['medical_record_number'], order['patient_name'],
#                      order['amount'], order['created_at'], order['status']])

#     response = make_response(si.getvalue())
#     response.headers['Content-Type'] = 'text/csv'
#     response.headers['Content-Disposition'] = 'attachment; filename=billing_history.csv'
#     return response




# def calculate_medication_total(prescriptions, db):
#     # Guard against None or empty string
#     if not prescriptions:
#         return 0

#     items = [item.strip() for item in prescriptions.split(',') if item.strip()]
#     total = 0
#     for item in items:
#         row = db.execute("SELECT price FROM medications WHERE name=?", (item,)).fetchone()
#         if row:
#             total += row['price']
#     return total


# def calculate_lab_total(patient_id, db):
#     rows = db.execute("""
#         SELECT test_name FROM lab_orders WHERE patient_id=? AND status='fulfilled'
#     """, (patient_id,)).fetchall()

#     if not rows:  # Guard against None or empty list
#         return 0

#     total = 0
#     for row in rows:
#         if not row['test_name']:
#             continue
#         test = db.execute("SELECT price FROM lab_tests WHERE name=?", (row['test_name'],)).fetchone()
#         if test:
#             total += test['price']
#     return total


# def calculate_admission_total(patient_id, db):
#     rows = db.execute("""
#         SELECT service FROM admissions WHERE patient_id=? AND status='active'
#     """, (patient_id,)).fetchall()

#     if not rows:  # Guard against None or empty list
#         return 0

#     total = 0
#     for row in rows:
#         if not row['service']:
#             continue
#         adm = db.execute("SELECT price FROM admissions WHERE service=?", (row['service'],)).fetchone()
#         if adm:
#             total += adm['price']
#     return total



# @app.route('/doctor/prescribe/<int:patient_id>', methods=['GET', 'POST'])
# def save_prescription(patient_id):
#     db = get_db()
#     if request.method == 'POST':
#         selected_ids = request.form.getlist('medications')
#         prescription_texts = []
#         total_amount = 0

#         for med_id in selected_ids:
#             med = db.execute("SELECT * FROM medications WHERE id=?", (med_id,)).fetchone()
#             if med:
#                 prescription_texts.append(f"{med['name']} {med['dosage']} - {med['instructions']}")
#                 total_amount += med['price']

#         prescription_str = "; ".join(prescription_texts)

#         # Save prescription
#         db.execute("""
#             INSERT INTO pharmacy_orders (patient_id, prescription, status, created_at)
#             VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
#         """, (patient_id, prescription_str))

#         # Also create cashier order with bill
#         db.execute("""
#             INSERT INTO cashier_orders (patient_id, amount, status, created_at)
#             VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
#         """, (patient_id, total_amount))

#         db.commit()
#         flash('Prescription saved and sent to pharmacy & cashier.')
#         return redirect(url_for('doctor'))

#     # GET: show form
#     medications = db.execute("SELECT * FROM medications").fetchall()
#     patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
#     return render_template('prescription_template.html', patient=patient, medications=medications)


# @app.route('/doctor/order/<int:patient_id>', methods=['GET', 'POST'])
# def save_order(patient_id):
#     db = get_db()
#     if request.method == 'POST':
#         med_ids = request.form.getlist('medications')
#         lab_ids = request.form.getlist('lab_tests')
#         adm_ids = request.form.getlist('admissions')

#         prescription_texts = []
#         total_amount = 0

#         # Medications
#         for med_id in med_ids:
#             med = db.execute("SELECT * FROM medications WHERE id=?", (med_id,)).fetchone()
#             if med:
#                 prescription_texts.append(f"{med['name']} {med['dosage']} - {med['instructions']}")
#                 total_amount += med['price']

#         # Lab Tests
#         for lab_id in lab_ids:
#             test = db.execute("SELECT * FROM lab_tests WHERE id=?", (lab_id,)).fetchone()
#             if test:
#                 prescription_texts.append(f"Lab Test: {test['name']}")
#                 total_amount += test['price']

#         # Admissions
#         for adm_id in adm_ids:
#             adm = db.execute("SELECT * FROM admission_services WHERE id=?", (adm_id,)).fetchone()
#             if adm:
#                 prescription_texts.append(f"Admission Service: {adm['service']}")
#                 total_amount += adm['price']

#         prescription_str = "; ".join(prescription_texts)

#         # Save pharmacy order
#         db.execute("""
#             INSERT INTO pharmacy_orders (patient_id, prescription, status, created_at)
#             VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
#         """, (patient_id, prescription_str))

#         # Save cashier order
#         db.execute("""
#             INSERT INTO cashier_orders (patient_id, amount, status, created_at)
#             VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
#         """, (patient_id, total_amount))

#         db.commit()
#         flash(f'Order saved. Total bill: KES {total_amount}')
#         return redirect(url_for('doctor'))

#     # GET: show form
#     medications = db.execute("SELECT * FROM medications").fetchall()
#     lab_tests = db.execute("SELECT * FROM lab_tests").fetchall()
#     admissions = db.execute("SELECT * FROM admission_services").fetchall()
#     patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
#     return render_template('prescription_template.html',
#                            patient=patient,
#                            medications=medications,
#                            lab_tests=lab_tests,
#                            admissions=admissions)


# # ---------------- Patient List ----------------

# @app.route('/patients')
# def patients():
#     db = get_db()
#     q = request.args.get('q', '').strip()

#     if q:
#         patients = db.execute("""
#             SELECT * FROM patients
#             WHERE is_active = 1
#               AND (first_name LIKE ? OR last_name LIKE ? OR medical_record_number LIKE ?)
#             ORDER BY created_at DESC
#         """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
#     else:
#         patients = db.execute("""
#             SELECT * FROM patients
#             WHERE is_active = 1
#             ORDER BY created_at DESC
#         """).fetchall()

#     return render_template('patients.html', patients=patients)


# @app.route('/patients/<int:id>')
# def patient_detail(id):
#     db = get_db()

#     # Patient record
#     patient = db.execute("SELECT * FROM patients WHERE id=?", (id,)).fetchone()
#     if not patient:
#         abort(404)

#     # Medical history
#     history = db.execute("""
#         SELECT diagnosis, symptoms, created_at
#         FROM medical_history
#         WHERE patient_id=?
#         ORDER BY created_at DESC
#     """, (id,)).fetchall()

#     # Last medication
#     last_med = db.execute("""
#         SELECT prescription, created_at
#         FROM pharmacy_orders
#         WHERE patient_id=?
#         ORDER BY created_at DESC
#         LIMIT 1
#     """, (id,)).fetchone()

#     return render_template(
#         'patient_detail.html',
#         patient=patient,
#         history=history,
#         last_med=last_med
#     )


# # ---------------- Additional Sidebar Routes ----------------
# # @app.route('/admission')
# # def admission():
# #     return render_template('admission.html')



# @app.route('/medical_reports')
# def medical_reports():
#     return render_template('medical_reports.html')

# # ---------------- Search ----------------
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

#         sql += " ORDER BY created_at DESC"
#         results = db.execute(sql, params).fetchall()

#     return render_template('search.html', results=results)

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)






# # @app.route('/pharmacy/fulfill', methods=['POST'])
# # def fulfill_pharmacy_order():
# #     order_id = request.form['order_id']
# #     db = get_db()
# #     db.execute("""
# #         UPDATE pharmacy_orders
# #         SET status = 'fulfilled', fulfilled_by = 'Pharmacist A', fulfilled_at = CURRENT_TIMESTAMP
# #         WHERE id = ?
# #     """, (order_id,))
# #     db.commit()
# #     flash('Order marked as fulfilled')
# #     return redirect(url_for('pharmacy'))

# # @app.route('/pharmacy')
# # def pharmacy():
# #     db = get_db()
# #     orders = db.execute("""
# #         SELECT po.id, p.medical_record_number,
# #                p.first_name || ' ' || p.last_name AS patient_name,
# #                po.prescription, po.ordered_by, po.created_at,
# #                po.status, po.fulfilled_by, po.fulfilled_at
# #         FROM pharmacy_orders po
# #         JOIN patients p ON po.patient_id = p.id
# #         ORDER BY po.created_at DESC
# #     """).fetchall()

# #     current_date = datetime.now().strftime('%A, %B %d, %Y')
# #     return render_template('pharmacy.html', orders=orders, current_date=current_date)


# # @app.route('/pharmacy/fulfill', methods=['POST'])
# # def fulfill_order():
# #     order_id = request.form['order_id']
# #     db = get_db()
# #     db.execute("""
# #         UPDATE pharmacy_orders
# #         SET status = 'fulfilled', fulfilled_by = 'Pharmacist A',
# #             fulfilled_at = CURRENT_TIMESTAMP
# #         WHERE id = ?
# #     """, (order_id,))
# #     db.commit()
# #     flash('Order marked as fulfilled')
# #     return redirect(url_for('pharmacy'))


# # @app.route('/cashier/mark_paid', methods=['POST'])
# # def mark_paid():
# #     order_id = request.form['order_id']
# #     db = get_db()

# #     patient = db.execute("""
# #         SELECT p.*, co.amount
# #         FROM cashier_orders co
# #         JOIN patients p ON co.patient_id = p.id
# #         WHERE co.id=?
# #     """, (order_id,)).fetchone()

# #     # Mark order as paid
# #     db.execute("UPDATE cashier_orders SET status='paid' WHERE id=?", (order_id,))
# #     db.execute("""
# #         UPDATE patients SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?
# #     """, (patient['id'],))
# #     db.commit()

# #     flash('Payment recorded successfully. Receipt generated.', 'success')
# #     return render_template('receipt.html', patient=patient, amount=patient['amount'])


# # @app.route('/cashier')
# # def cashier():
# #     db = get_db()
# #     orders = db.execute("""
# #         SELECT co.id, p.medical_record_number,
# #                p.first_name || ' ' || p.last_name AS patient_name,
# #                co.amount, co.created_at, co.status
# #         FROM cashier_orders co
# #         JOIN patients p ON co.patient_id = p.id
# #         WHERE co.status = 'pending'
# #         ORDER BY co.created_at ASC
# #     """).fetchall()

# #     current_date = datetime.now().strftime('%A, %B %d, %Y')
# #     return render_template('cashier.html', orders=orders, current_date=current_date)



# # @app.route('/cashier/mark_paid', methods=['POST'])
# # def mark_paid():
# #     order_id = request.form['order_id']
# #     db = get_db()

# #     patient_id = db.execute("SELECT patient_id FROM cashier_orders WHERE id=?", (order_id,)).fetchone()['patient_id']

# #     db.execute("UPDATE cashier_orders SET status='paid' WHERE id=?", (order_id,))
# #     db.execute("""
# #         UPDATE patients SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?
# #     """, (patient_id,))
# #     db.commit()

# #     flash('Payment recorded successfully. Patient completed.')
# #     return redirect(url_for('cashier'))

# # @app.route('/cashier/mark_paid', methods=['POST'])
# # def mark_paid():
# #     order_id = request.form['order_id']
# #     db = get_db()
# #     db.execute("""
# #         UPDATE cashier_orders
# #         SET status = 'paid'
# #         WHERE id = ?
# #     """, (order_id,))
# #     db.commit()
# #     flash('Payment recorded successfully.')
# #     return redirect(url_for('cashier'))


# # @app.route('/cashier', methods=['GET', 'POST'])
# # def cashier():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         bill_amount = request.form['bill_amount']
# #         db = get_db()
# #         db.execute("UPDATE patients SET bill_amount = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (bill_amount, patient_id))
# #         db.commit()
# #         flash('Bill paid successfully!')
# #         return redirect(url_for('cashier'))
# #     return render_template('cashier.html')


# # @app.route('/patient/<int:id>')
# # def patient_detail(id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
# #     db.close()

# #     if not patient:
# #         flash("Patient not found.", "danger")
# #         return redirect(url_for('checkin'))

# #     return render_template('patient_detail.html', patient=patient)


# # billing history.....................

# # @app.route('/cashier/history')
# # def billing_history():
# #     db = get_db()
# #     orders = db.execute("""
# #         SELECT co.id, p.medical_record_number,
# #                p.first_name || ' ' || p.last_name AS patient_name,
# #                co.amount, co.created_at, co.status
# #         FROM cashier_orders co
# #         JOIN patients p ON co.patient_id = p.id
# #         WHERE co.status = 'paid'
# #         ORDER BY co.created_at DESC
# #     """).fetchall()

# #     current_date = datetime.now().strftime('%A, %B %d, %Y')
# #     return render_template('billing_history.html', orders=orders, current_date=current_date)

# # @app.route('/patients')
# # def patients():
# #     db = get_db()
# #     patients = db.execute(
# #         "SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC"
# #     ).fetchall()
# #     return render_template('patients.html', patients=patients)

# # # @app.route('/patients/<int:id>')
# # # def patient_detail(id):
# # #     db = get_db()
# # #     patient = db.execute("SELECT * FROM patients WHERE id=?", (id,)).fetchone()
# # #     if not patient:
# # #         abort(404)
# # #     return render_template('patient_detail.html', patient=patient)
# # @app.route('/patients/<int:id>')
# # def patient_detail(id):
# #     db = get_db()

# #     # Get patient record
# #     patient = db.execute("SELECT * FROM patients WHERE id=?", (id,)).fetchone()
# #     if not patient:
# #         abort(404)

# #     # Get medical history (visits, diagnoses, etc.)
# #     history = db.execute("""
# #         SELECT diagnosis, symptoms, created_at
# #         FROM medical_history
# #         WHERE patient_id=?
# #         ORDER BY created_at DESC
# #     """, (id,)).fetchall()

# #     # Get last medication prescribed
# #     last_med = db.execute("""
# #         SELECT prescription, created_at
# #         FROM pharmacy_orders
# #         WHERE patient_id=?
# #         ORDER BY created_at DESC
# #         LIMIT 1
# #     """, (id,)).fetchone()

# #     return render_template(
# #         'patient_detail.html',
# #         patient=patient,
# #         history=history,
# #         last_med=last_med
# #     )


# # @app.route('/patients')
# # def patients():
# #     db = get_db()
# #     patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
# #     return render_template('patients.html', patients=patients)

# # @app.route('/lab/fulfill', methods=['POST'])
# # def fulfill_lab_order():
# #     order_id = request.form['order_id']
# #     lab_results = request.form['lab_results']
# #     db = get_db()

# #     # Find patient linked to this order
# #     patient_id = db.execute("SELECT patient_id FROM lab_orders WHERE id = ?", (order_id,)).fetchone()['patient_id']

# #     # Save results in patient record
# #     db.execute("""
# #         UPDATE patients
# #         SET lab_results = ?, updated_at = CURRENT_TIMESTAMP
# #         WHERE id = ?
# #     """, (lab_results, patient_id))

# #     # Mark lab order as fulfilled
# #     db.execute("""
# #         UPDATE lab_orders
# #         SET status = 'fulfilled', fulfilled_at = CURRENT_TIMESTAMP
# #         WHERE id = ?
# #     """, (order_id,))
# #     db.commit()

# #     flash('Lab results saved and patient sent back to doctor.')
# #     return redirect(url_for('lab'))


# # app = Flask(__name__)

# # def get_db():
# #     # your DB connection logic here
# #     pass

# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     generated_mrn = f"MRN{int(time.time())}"

# #     if request.method == 'POST':
# #         card_number = request.form.get('card_number')
# #         if not card_number:
# #             flash('Please enter a card number.', 'danger')
# #             return redirect(url_for('checkin'))

# #         db = get_db()
# #         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()

# #         if patient:
# #             # Get last visit date
# #             last_visit = db.execute("""
# #                 SELECT MAX(appointment_date) AS last_visit
# #                 FROM appointments
# #                 WHERE patient_id = ?
# #             """, (patient['id'],)).fetchone()

# #             # Get last prescription
# #             last_prescription = db.execute("""
# #                 SELECT prescriptions, updated_at
# #                 FROM patients
# #                 WHERE id = ?
# #             """, (patient['id'],)).fetchone()

# #             # Queue patient if not already queued today
# #             existing_appt = db.execute("""
# #                 SELECT id FROM appointments 
# #                 WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
# #             """, (patient['id'],)).fetchone()

# #             if not existing_appt:
# #                 db.execute("""
# #                     INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #                     VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #                 """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic
# #                 db.commit()

# #             return render_template(
# #                 'checkin_details.html',
# #                 patient=patient,
# #                 last_visit=last_visit['last_visit'] if last_visit else None,
# #                 last_prescription=last_prescription['prescriptions'] if last_prescription else None,
# #                 generated_mrn=generated_mrn
# #             )
# #         else:
# #             flash(f"No patient found with card number: {card_number}. Please register.", 'warning')
# #             return redirect(url_for('register'))

# #     return render_template('checkin.html', generated_mrn=generated_mrn)




# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()

# #     if request.method == 'POST':
# #         data = request.form
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         # Generate card number automatically
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         card_number = f"HCO{next_id:05d}"   # Example: HCO00001, HCO00002, etc.
# #         mrn = f"MRN{next_id:05d}"

# #         full_name = f"{data['first_name']} {data['last_name']}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn,
# #             card_number,
# #             full_name,
# #             data['first_name'],
# #             data['last_name'],
# #             age,
# #             data['gender'],
# #             data['contact'],
# #             data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         # Queue patient for doctor immediately
# #         db.execute("""
# #             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #         """, (new_id, 1))
# #         db.commit()

# #         flash(f'Patient registered successfully! Card Number: {card_number}', 'success')
# #         return redirect(url_for('print_card', patient_id=new_id))

# #     # GET request — generate MRN preview
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn)


# # @app.route('/print_card/<int:patient_id>')
# # def print_card(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
# #     return render_template('patient_card.html', patient=patient)

# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     generated_mrn = f"MRN{int(time.time())}"

# #     if request.method == 'POST':
# #         card_number = request.form.get('card_number')
# #         if not card_number:
# #             flash('Please enter a card number.', 'danger')
# #             return redirect(url_for('checkin'))

# #         db = get_db()
# #         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()

# #         if patient:
# #             # Check if already queued today
# #             existing_appt = db.execute("""
# #                 SELECT id FROM appointments 
# #                 WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
# #             """, (patient['id'],)).fetchone()

# #             if not existing_appt:
# #                 db.execute("""
# #                     INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #                     VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #                 """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic
# #                 db.commit()

# #                 try:
# #                     sms.send(f"{patient['first_name']} {patient['last_name']} has been queued for doctor review.", [patient['contact']])
# #                 except Exception as e:
# #                     print("SMS failed:", e)

# #             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
# #             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
# #         else:
# #             flash(f"No patient found with card number: {card_number}. Please register.", 'warning')
# #             return redirect(url_for('register'))

# #     return render_template('checkin.html', generated_mrn=generated_mrn)


# # @app.route('/send_to_lab/<int:patient_id>', methods=['POST'])
# # def send_to_lab(patient_id):
# #     test_name = request.form.get('test_name', 'General Test')
# #     db = get_db()
# #     db.execute("""
# #         INSERT INTO lab_orders (patient_id, test_name, ordered_by, created_at)
# #         VALUES (?, ?, ?, CURRENT_TIMESTAMP)
# #     """, (patient_id, test_name, 'Dr. Wanyama'))
# #     db.commit()
# #     flash('Lab test ordered successfully')
# #     return redirect(url_for('doctor'))


# # @app.route('/release')
# # def release():
# #     return render_template('release.html')

# # ---------------- Patient Registration ----------------
# # from datetime import datetime
# # import time



# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     generated_mrn = f"MRN{int(time.time())}"

# #     if request.method == 'POST':
# #         card_number = request.form.get('card_number')
# #         if not card_number:
# #             flash('Please enter a card number.', 'danger')
# #             return redirect(url_for('checkin'))

# #         db = get_db()
# #         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()

# #         if patient:
# #             # Check if already queued today
# #             existing_appt = db.execute("""
# #                 SELECT id FROM appointments 
# #                 WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
# #             """, (patient['id'],)).fetchone()

# #             if not existing_appt:
# #                 db.execute("""
# #                     INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #                     VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #                 """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic
# #                 db.commit()

# #                 try:
# #                     sms.send(f"{patient['first_name']} {patient['last_name']} has been queued for doctor review.", [patient['contact']])
# #                 except Exception as e:
# #                     print("SMS failed:", e)

# #             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
# #             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
# #         else:
# #             flash(f"No patient found with card number: {card_number}", 'warning')
# #             return redirect(url_for('checkin'))

# #     return render_template('checkin.html', generated_mrn=generated_mrn)



# # from datetime import datetime
# # import time

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()

# #     if request.method == 'POST':
# #         data = request.form
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address', 'card_number']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         # Check for duplicate contact or card number
# #         existing = db.execute("SELECT id FROM patients WHERE contact = ? OR card_number = ?", 
# #                               (data['contact'], data['card_number'])).fetchone()
# #         if existing:
# #             flash('A patient with this contact or card number already exists.', 'warning')
# #             return redirect(url_for('register'))

# #         full_name = f"{data['first_name']} {data['last_name']}"
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn,
# #             data['card_number'],
# #             full_name,
# #             data['first_name'],
# #             data['last_name'],
# #             age,
# #             data['gender'],
# #             data['contact'],
# #             data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         flash('Patient registered successfully!', 'success')
# #         return redirect(url_for('print_card', patient_id=new_id))

# #     # GET request — generate MRN for display
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card)




# # # ......................printcard.............................
# # @app.route('/print_card/<int:patient_id>')
# # def print_card(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
# #     return render_template('patient_card.html', patient=patient)


# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()

# #     if request.method == 'POST':
# #         data = request.form
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address', 'card_number']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         # Check for duplicate contact or card number
# #         existing = db.execute("SELECT id FROM patients WHERE contact = ? OR card_number = ?", 
# #                               (data['contact'], data['card_number'])).fetchone()
# #         if existing:
# #             flash('A patient with this contact or card number already exists.', 'warning')
# #             return redirect(url_for('checkin'))

# #         full_name = f"{data['first_name']} {data['last_name']}"
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, card_number, name, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn,
# #             data['card_number'],
# #             full_name,
# #             data['first_name'],
# #             data['last_name'],
# #             age,
# #             data['gender'],
# #             data['contact'],
# #             data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         # Queue patient for doctor immediately
# #         db.execute("""
# #             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
# #         db.commit()

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}. You have been queued for doctor review.", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         flash('Patient registered and queued successfully!', 'success')
# #         return redirect(url_for('doctor_dashboard', patient_id=new_id))

# #     # GET request — generate MRN for display
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn)


# # ....................send to pharmacy.............................
# # @app.route('/send_to_pharmacy/<int:patient_id>')
# # def send_to_pharmacy(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

# #     # Record pharmacy order
# #     db.execute("""
# #         INSERT INTO pharmacy_orders (patient_id, ordered_by, created_at, status)
# #         VALUES (?, ?, CURRENT_TIMESTAMP, 'pending')
# #     """, (patient_id, 'Dr. Wanyama'))
# #     db.commit()

# #     flash(f"Patient {patient['first_name']} {patient['last_name']} sent to pharmacy.", 'success')
# #     return redirect(url_for('doctor'))


# # @app.route('/doctor', methods=['GET', 'POST'])
# # def doctor():
# #     db = get_db()

# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
# #         db.execute("""
# #             UPDATE patients 
# #             SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP 
# #             WHERE id = ?
# #         """, (symptoms, diagnosis, patient_id))
# #         db.commit()
# #         flash('Diagnosis saved successfully!')
# #         return redirect(url_for('doctor'))

# #     today_patients = db.execute("""
# #         SELECT patients.id AS patient_id, first_name || ' ' || last_name AS name
# #         FROM appointments
# #         JOIN patients ON appointments.patient_id = patients.id
# #         WHERE DATE(appointments.appointment_date) = DATE('now') AND appointments.status = 'scheduled'
# #         ORDER BY appointments.appointment_date ASC
# #     """).fetchall()

# #     current_date = datetime.now().strftime('%A, %B %d, %Y')
# #     return render_template('doctor.html', patients=today_patients, current_date=current_date)


# # @app.route('/doctor/examine/<int:patient_id>', methods=['GET', 'POST'])
# # def examine_patient(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

# #     if request.method == 'POST':
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
# #         prescriptions = request.form['prescriptions']
# #         tests = request.form['tests']

# #         db.execute("""
# #             UPDATE patients 
# #             SET symptoms = ?, diagnosis = ?, prescriptions = ?, tests_ordered = ?, updated_at = CURRENT_TIMESTAMP 
# #             WHERE id = ?
# #         """, (symptoms, diagnosis, prescriptions, tests, patient_id))
# #         db.commit()
# #         flash('Patient updated successfully!')
# #         return redirect(url_for('doctor'))

# #     return render_template('examine.html', patient=patient)


# # @app.route('/doctor/autosave/<int:patient_id>', methods=['POST'])
# # def autosave(patient_id):
# #     data = request.get_json()
# #     db = get_db()
# #     db.execute("""
# #         UPDATE patients SET symptoms = ?, diagnosis = ?, prescriptions = ?, tests_ordered = ?, status = 'draft', updated_at = CURRENT_TIMESTAMP 
# #         WHERE id = ?
# #     """, (data['symptoms'], data['diagnosis'], data['prescriptions'], data['tests'], patient_id))
# #     db.commit()
# #     return jsonify({'message': 'Draft saved'})




# # @app.route('/doctor/prescription/<int:patient_id>')
# # def prescription_pdf(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
# #     html = render_template('prescription_template.html', patient=patient)
# #     pdf = HTML(string=html).write_pdf()
# #     response = make_response(pdf)
# #     response.headers['Content-Type'] = 'application/pdf'
# #     response.headers['Content-Disposition'] = f'inline; filename=prescription_{patient_id}.pdf'
# #     return response


# # @app.route('/lab/order', methods=['POST'])
# # def order_lab_test():
# #     patient_id = request.form['patient_id']
# #     test_name = request.form['test_name']
# #     db = get_db()
# #     db.execute("INSERT INTO lab_orders (patient_id, test_name, ordered_by) VALUES (?, ?, ?)",
# #                (patient_id, test_name, 'Dr. Wanyama'))
# #     db.commit()
# #     flash('Lab test ordered successfully')
# #     return redirect(url_for('doctor'))

# # @app.route('/doctor/<int:patient_id>')
# # def doctor_dashboard(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
# #     return render_template('doctor_dashboard.html', patient=patient)

# # # ....................notify.............................
# # @app.route('/notify_doctor_ready/<int:appointment_id>')
# # def notify_doctor_ready(appointment_id):
# #     db = get_db()
# #     appointment = db.execute("""
# #         SELECT a.*, d.contact AS doctor_contact, p.first_name || ' ' || p.last_name AS patient_name
# #         FROM appointments a
# #         JOIN doctors d ON a.doctor_id = d.id
# #         JOIN patients p ON a.patient_id = p.id
# #         WHERE a.id = ?
# #     """, (appointment_id,)).fetchone()

# #     try:
# #         sms.send(f"Patient {appointment['patient_name']} is ready for examination.", [appointment['doctor_contact']])
# #         flash('Doctor notified successfully.', 'success')
# #     except Exception as e:
# #         print("SMS failed:", e)
# #         flash('Failed to notify doctor.', 'danger')

# #     return redirect(url_for('dashboard'))



# # @app.route('/doctor_ready/<int:appointment_id>')
# # def doctor_ready(appointment_id):
# #     db = get_db()
# #     appointment = db.execute("""
# #         SELECT a.*, p.contact AS patient_contact
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         WHERE a.id = ?
# #     """, (appointment_id,)).fetchone()

# #     try:
# #         sms.send(f"Doctor is ready to see you now.", [appointment['patient_contact']])
# #         flash('Patient notified.', 'success')
# #     except Exception as e:
# #         print("SMS failed:", e)
# #         flash('Failed to notify patient.', 'danger')

# #     return redirect(url_for('doctor'))

# # ---------------- Laboratory ----------------
# # from functools import wraps
# # from flask import abort
# # from flask_login import current_user

# # @app.route('/lab', methods=['GET', 'POST'])
# # def lab():
# #     db = get_db()

# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         lab_results = request.form['lab_results']
# #         db.execute("UPDATE patients SET lab_results = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (lab_results, patient_id))
# #         db.commit()
# #         flash('Lab results saved successfully!')
# #         return redirect(url_for('lab'))

# #     patients = db.execute("SELECT id, first_name || ' ' || last_name AS name FROM patients").fetchall()
# #     recent_entries = db.execute("""
# #         SELECT patients.first_name || ' ' || patients.last_name AS name,
# #                patients.lab_results,
# #                patients.updated_at
# #         FROM patients
# #         WHERE lab_results IS NOT NULL
# #         ORDER BY updated_at DESC
# #         LIMIT 10
# #     """).fetchall()

# #     current_date = datetime.now().strftime('%A, %B %d, %Y')
# #     return render_template('lab.html', patients=patients, recent_entries=recent_entries, current_date=current_date)


# # # ---------------- Pharmacy ----------------
# # @app.route('/pharmacy', methods=['GET', 'POST'])
# # def pharmacy():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         prescribed_medicine = request.form['prescribed_medicine']
# #         db = get_db()
# #         db.execute("UPDATE patients SET prescribed_medicine = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (prescribed_medicine, patient_id))
# #         db.commit()
# #         flash('Prescribed medicine saved successfully!')
# #         return redirect(url_for('pharmacy'))
# #     return render_template('pharmacy.html')


# # @app.route('/pharmacy/order', methods=['POST'])
# # def pharmacy_order():
# #     patient_id = request.form['patient_id']
# #     prescription = request.form['prescription']
# #     ordered_by = 'Dr. Wanyama'  # Replace with session user if using login
# #     db = get_db()
# #     db.execute("""
# #         INSERT INTO pharmacy_orders (patient_id, prescription, ordered_by)
# #         VALUES (?, ?, ?)
# #     """, (patient_id, prescription, ordered_by))
# #     db.commit()
# #     flash('Prescription sent to pharmacy')
# #     return redirect(url_for('doctor'))


# # @app.route('/pharmacy')
# # def pharmacy_dashboard():
# #     db = get_db()
# #     orders = db.execute("""
# #         SELECT po.*, p.first_name || ' ' || p.last_name AS patient_name
# #         FROM pharmacy_orders po
# #         JOIN patients p ON po.patient_id = p.id
# #         ORDER BY po.created_at DESC
# #     """).fetchall()
# #     return render_template('pharmacy.html', orders=orders)


# # @app.route('/pharmacy/fulfill', methods=['POST'])
# # def fulfill_order():
# #     order_id = request.form['order_id']
# #     db = get_db()
# #     db.execute("""
# #         UPDATE pharmacy_orders 
# #         SET status = 'fulfilled', fulfilled_by = 'Pharmacist A', fulfilled_at = CURRENT_TIMESTAMP 
# #         WHERE id = ?
# #     """, (order_id,))
# #     db.commit()
# #     flash('Order marked as fulfilled')
# #     return redirect(url_for('pharmacy_dashboard'))

# # def order_lab_test():
# #     patient_id = request.form['patient_id']
# #     test_name = request.form['test_name']
# #     db = get_db()
# #     db.execute("INSERT INTO lab_orders (patient_id, test_name, ordered_by) VALUES (?, ?, ?)",
# #                (patient_id, test_name, 'Dr. Wanyama'))
# #     db.commit()
# #     flash('Lab test ordered successfully')
# #     return redirect(url_for('doctor'))



# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     generated_mrn = f"MRN{int(time.time())}"  # Used for new patient registration modal

# #     if request.method == 'POST':
# #         card_number = request.form.get('card_number')
# #         if not card_number:
# #             flash('Please enter a card number.', 'danger')
# #             return redirect(url_for('checkin'))

# #         db = get_db()
# #         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()
# #         db.close()

# #         if patient:
# #             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
# #             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
# #         else:
# #             flash(f"Patient Not Found - No patient found with card number: {card_number}", 'warning')
# #             return redirect(url_for('checkin'))

# #     # GET request — show check-in page with generated MRN
# #     return render_template('checkin.html', generated_mrn=generated_mrn)


# # return render_template('register.html', generated_mrn=generated_mrn)

# # from datetime import datetime
# # import time

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()

# #     if request.method == 'POST':
# #         data = request.form

# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.', 'warning')
# #             return redirect(url_for('register'))

# #         full_name = f"{data['first_name']} {data['last_name']}"
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn,
# #             full_name,
# #             data['first_name'],
# #             data['last_name'],
# #             age,
# #             data['gender'],
# #             data['contact'],
# #             data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         flash('Patient registered successfully!', 'success')
# #         return redirect(url_for('register', show_modal='true', patient_id=new_id))

# #     # GET request — generate MRN for display
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn, patient_card=None)


# #  @app.route('/print_card/<int:patient_id>')
# # def print_card(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
# #     return render_template('patient_card.html', patient=patient)

# # @app.route('/print_card/<int:patient_id>')
# # def print_card(patient_id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
# #     return render_template('patient_card.html', patient=patient)

# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     generated_mrn = f"MRN{int(time.time())}"

# #     if request.method == 'POST':
# #         card_number = request.form.get('card_number')
# #         if not card_number:
# #             flash('Please enter a card number.', 'danger')
# #             return redirect(url_for('checkin'))

# #         db = get_db()
# #         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()

# #         if patient:
# #             # Queue if not already
# #             existing_appt = db.execute("""
# #                 SELECT id FROM appointments WHERE patient_id = ? AND DATE(appointment_date) = DATE('now')
# #             """, (patient['id'],)).fetchone()

# #             if not existing_appt:
# #                 db.execute("""
# #                     INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #                     VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #                 """, (patient['id'], 1))  # Replace 1 with actual doctor_id logic
# #                 db.commit()

# #             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
# #             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
# #         else:
# #             flash(f"No patient found with card number: {card_number}", 'warning')
# #             return redirect(url_for('checkin'))

# #     return render_template('checkin.html', generated_mrn=generated_mrn)





# # @app.route('/doctor', methods=['GET', 'POST'])
# # def doctor():
# #     db = get_db()

# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
# #         db.execute("""
# #             UPDATE patients 
# #             SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP 
# #             WHERE id = ?
# #         """, (symptoms, diagnosis, patient_id))
# #         db.commit()
# #         flash('Diagnosis saved successfully!')
# #         return redirect(url_for('doctor'))

# #     # Fetch today's patients (example logic)
# #     today_patients = db.execute("""
# #     SELECT patients.id AS patient_id,
# #            first_name || ' ' || last_name AS name 
# #     FROM appointments 
# #     JOIN patients ON appointments.patient_id = patients.id 
# #     WHERE DATE(appointments.appointment_date) = DATE('now')
# # """).fetchall()


# #     current_date = datetime.now().strftime('%A, %B %d, %Y')
# #     return render_template('doctor.html', patients=today_patients, current_date=current_date)




# # from datetime import datetime
# # import time

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()
# #     patient_card = None  # ✅ Define it early so it's available in both GET and POST

# #     if request.method == 'POST':
# #         data = request.form
# #         required_fields = ['first_name', 'last_name', 'dob', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]

# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             dob = datetime.strptime(data['dob'], '%Y-%m-%d')
# #             today = datetime.today()
# #             age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid date of birth.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Date of birth must be in YYYY-MM-DD format.', 'warning')
# #             return redirect(url_for('register'))

# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.', 'warning')
# #             return redirect(url_for('register'))

# #         full_name = f"{data['first_name']} {data['last_name']}"
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn, full_name, data['first_name'], data['last_name'], age,
# #             data['gender'], data['contact'], data['address']
# #         ))
# #         db.commit()

# #         new_id = cursor.lastrowid

# #         db.execute("""
# #             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
# #         db.commit()

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         patient_card = db.execute("SELECT * FROM patients WHERE id = ?", (new_id,)).fetchone()
# #         flash('Patient registered and queued successfully!', 'success')
# #         return render_template('register.html', generated_mrn=mrn, patient_card=patient_card, show_modal='true')

# #     # GET request — show empty registration form
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card)


# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()

# #     if request.method == 'POST':
# #         data = request.form
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.', 'warning')
# #             return redirect(url_for('register'))

# #         full_name = f"{data['first_name']} {data['last_name']}"
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn, full_name, data['first_name'], data['last_name'], age,
# #             data['gender'], data['contact'], data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         # Queue patient to doctor
# #         db.execute("""
# #             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
# #         db.commit()

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         patient_card = db.execute("SELECT * FROM patients WHERE id = ?", (new_id,)).fetchone()
# #         flash('Patient registered and queued successfully!', 'success')
# #         return render_template('register.html', generated_mrn=mrn, patient_card=patient_card, show_modal='true')

# #     # GET request — show empty registration form
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card)

#     # return render_template('register.html', generated_mrn=generated_mrn)

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()

# #     if request.method == 'POST':
# #         data = request.form
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.', 'warning')
# #             return redirect(url_for('register'))

# #         full_name = f"{data['first_name']} {data['last_name']}"
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, name, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn, full_name, data['first_name'], data['last_name'], age,
# #             data['gender'], data['contact'], data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         # Queue patient to doctor
# #         db.execute("""
# #             INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
# #             VALUES (?, ?, CURRENT_TIMESTAMP, 'scheduled')
# #         """, (new_id, 1))  # Replace 1 with actual doctor_id logic
# #         db.commit()

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         flash('Patient registered and queued successfully!', 'success')
# #         return redirect(url_for('print_card', patient_id=new_id))

# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn)
# #     patient_card = db.execute("SELECT * FROM patients WHERE id = ?", (new_id,)).fetchone()
# #     return render_template('register.html', generated_mrn=generated_mrn, patient_card=patient_card, show_modal='true')



# # from datetime import datetime
# # import time

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()

# #     if request.method == 'POST':
# #         data = request.form

# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.', 'warning')
# #             return redirect(url_for('register'))

# #         full_name = f"{data['first_name']} {data['last_name']}"

# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn,
# #             data['first_name'],
# #             data['last_name'],
# #             age,
# #             data['gender'],
# #             data['contact'],
# #             data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         # flash('Patient registered successfully!', 'success')
# #         # return redirect(url_for('doctor_dashboard', patient_id=new_id))
# #         flash('Patient registered successfully!', 'success')
# #         return redirect(url_for('register', show_modal='true', patient_id=new_id))


# #     # GET request — generate MRN for display
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('register.html', generated_mrn=generated_mrn, patient_card=None)
# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     ...
# #     generated_mrn = f"MRN{int(time.time())}"
# #     return render_template('checkin.html', generated_mrn=generated_mrn)

# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     if request.method == 'POST':
# #         card_number = request.form.get('card_number')
# #         if not card_number:
# #             flash('Please enter a card number.', 'danger')
# #             return redirect(url_for('checkin'))

# #         db = get_db()
# #         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()
# #         db.close()

# #         if patient:
# #             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
# #             # Redirect to doctor dashboard with patient ID
# #             return redirect(url_for('doctor_dashboard', patient_id=patient['id']))
# #         else:
# #             flash(f"Patient Not Found - No patient found with card number: {card_number}", 'warning')
# #             return redirect(url_for('checkin'))

# #     return render_template('checkin.html')





# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     db = get_db()
# #     generated_mrn = f"MRN{int(time.time())}"  # Default MRN for GET

# #     if request.method == 'POST':
# #         data = request.form
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]

# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return render_template('checkin.html', generated_mrn=generated_mrn)

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return render_template('checkin.html', generated_mrn=generated_mrn)
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return render_template('checkin.html', generated_mrn=generated_mrn)

# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.', 'warning')
# #             return render_template('checkin.html', generated_mrn=generated_mrn)

# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn, data['first_name'], data['last_name'], age,
# #             data['gender'], data['contact'], data['address']
# #         ))
# #         db.commit()

# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         flash(f'Patient registered successfully! MRN: {mrn}', 'success')
# #         return render_template('checkin.html', generated_mrn=mrn)

# #     return render_template('checkin.html', generated_mrn=generated_mrn)




# # @app.route('/checkin', methods=['GET', 'POST'])
# # def checkin():
# #     if request.method == 'POST':
# #         card_number = request.form.get('card_number')
# #         if not card_number:
# #             flash('Please enter a card number.', 'danger')
# #             return redirect(url_for('checkin'))

# #         db = get_db()
# #         patient = db.execute('SELECT * FROM patients WHERE card_number = ?', (card_number,)).fetchone()
# #         db.close()

# #         if patient:
# #             flash(f"Patient found: {patient['first_name']} {patient['last_name']}", 'success')
# #         else:
# #             flash('No patient found with that card number.', 'warning')

# #         return redirect(url_for('checkin'))

# #     return render_template('checkin.html')

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         data = request.form
# #         db = get_db()

# #         # Validate required fields
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}", 'danger')
# #             return redirect(url_for('register'))

# #         # Validate age
# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.', 'warning')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.', 'warning')
# #             return redirect(url_for('register'))

# #         # Check for duplicate contact
# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.', 'warning')
# #             return redirect(url_for('register'))

# #         # Generate MRN
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         # Insert patient
# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn,
# #             data['first_name'],
# #             data['last_name'],
# #             age,
# #             data['gender'],
# #             data['contact'],
# #             data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         # Optional: Send SMS
# #         try:
# #             sms.send(f"Welcome to Wauguzi Hospital. Your MRN is {mrn}", [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         flash('Patient registered successfully!', 'success')
# #         return redirect(url_for('patient_detail', id=new_id))

# #     return render_template('register.html')


#     # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         data = request.form
# #         db = get_db()

# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}")
# #             return redirect(url_for('register'))

# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.')
# #             return redirect(url_for('register'))

# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.')
# #             return redirect(url_for('register'))

# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         cursor = db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             mrn,
# #             data['first_name'],
# #             data['last_name'],
# #             age,
# #             data['gender'],
# #             data['contact'],
# #             data['address']
# #         ))
# #         db.commit()
# #         new_id = cursor.lastrowid

# #         try:
# #             sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])
# #         except Exception as e:
# #             print("SMS failed:", e)

# #         flash('Patient registered successfully!')
# #         return redirect(url_for('patient_detail', id=new_id))

# #     return render_template('register.html')

# # if __name__ == '__main__':
# #     app.run(debug=True)


# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3
# # from datetime import datetime
# # import africastalking

# # # Initialize SDK
# # africastalking.initialize(username="your_username", api_key="your_api_key")
# # sms = africastalking.SMS

# # # Send SMS
# # sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])


# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

# # # ---------------- Database Connection ----------------
# # def get_db():
# #     conn = sqlite3.connect('hospital.db')
# #     conn.row_factory = sqlite3.Row
# #     return conn

# # # ---------------- Dashboard ----------------
# # @app.route('/')
# # def dashboard():
# #     db = get_db()
# #     today_sql = datetime.now().strftime('%Y-%m-%d')
# #     today_display = datetime.now().strftime('%A, %B %d, %Y')

# #     stats = {
# #         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
# #         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
# #         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
# #         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
# #         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today_sql,)).fetchone()[0],
# #         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
# #         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
# #         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
# #         'efficiency': 0
# #     }

# #     if stats['today_appointments'] > 0:
# #         stats['efficiency'] = round((stats['completed_appointments_today'] / stats['today_appointments']) * 100, 2)

# #     appointments = db.execute("""
# #         SELECT a.*, 
# #                p.first_name || ' ' || p.last_name AS patient_name,
# #                d.first_name || ' ' || d.last_name AS doctor_name,
# #                strftime('%H:%M', a.appointment_date) AS time
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         JOIN doctors d ON a.doctor_id = d.id
# #         WHERE DATE(a.appointment_date) = ?
# #         ORDER BY a.appointment_date ASC
# #     """, (today_sql,)).fetchall()

# #     return render_template('dashboard.html', stats=stats, appointments=appointments, current_date=today_display)

# # # ---------------- Patient Registration ----------------

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         data = request.form
# #         db = get_db()

# #         # Required field check
# #         required_fields = ['first_name', 'last_name', 'age', 'gender', 'contact', 'address']
# #         missing = [field for field in required_fields if not data.get(field)]
# #         if missing:
# #             flash(f"Missing fields: {', '.join(missing)}")
# #             return redirect(url_for('register'))

# #         # Age validation
# #         try:
# #             age = int(data['age'])
# #             if age < 0 or age > 120:
# #                 flash('Please enter a valid age between 0 and 120.')
# #                 return redirect(url_for('register'))
# #         except ValueError:
# #             flash('Age must be a number.')
# #             return redirect(url_for('register'))

# #         # Duplicate contact check
# #         existing = db.execute("SELECT id FROM patients WHERE contact = ?", (data['contact'],)).fetchone()
# #         if existing:
# #             flash('A patient with this contact already exists.')
# #             return redirect(url_for('register'))

# #         # Generate MRN
# #         last = db.execute("SELECT MAX(id) FROM patients").fetchone()[0]
# #         next_id = (last or 0) + 1
# #         mrn = f"MRN{next_id:05d}"

# #         # Insert patient

# #         # Insert patient
# # cursor = db.execute("""
# #     INSERT INTO patients (
# #         medical_record_number, first_name, last_name, age, gender, contact, address,
# #         is_active, created_at, updated_at
# #     ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# # """, (
# #     mrn,
# #     data['first_name'],
# #     data['last_name'],
# #     age,
# #     data['gender'],
# #     data['contact'],
# #     data['address']
# # ))
# # db.commit()
# # new_id = cursor.lastrowid

# # # ✅ Send SMS inside the route
# # try:
# #     sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])
# # except Exception as e:
# #     print("SMS failed:", e)

# # flash('Patient registered successfully!')
# # return redirect(url_for('patient_detail', id=new_id))



# # # ---------------- Doctor Interface ----------------
# # @app.route('/doctor', methods=['GET', 'POST'])
# # def doctor():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
# #         db = get_db()
# #         db.execute("UPDATE patients SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (symptoms, diagnosis, patient_id))
# #         db.commit()
# #         flash('Diagnosis saved successfully!')
# #         return redirect(url_for('doctor'))
# #     return render_template('doctor.html')

# # # ---------------- Laboratory ----------------
# # @app.route('/lab', methods=['GET', 'POST'])
# # def lab():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         lab_results = request.form['lab_results']
# #         db = get_db()
# #         db.execute("UPDATE patients SET lab_results = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (lab_results, patient_id))
# #         db.commit()
# #         flash('Lab results saved successfully!')
# #         return redirect(url_for('lab'))
# #     return render_template('lab.html')

# # # ---------------- Pharmacy ----------------
# # @app.route('/pharmacist', methods=['GET', 'POST'])
# # def pharmacist():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         prescribed_medicine = request.form['prescribed_medicine']
# #         db = get_db()
# #         db.execute("UPDATE patients SET prescribed_medicine = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (prescribed_medicine, patient_id))
# #         db.commit()
# #         flash('Prescribed medicine saved successfully!')
# #         return redirect(url_for('pharmacist'))
# #     return render_template('pharmacist.html')

# # # ---------------- Billing ----------------
# # @app.route('/cashier', methods=['GET', 'POST'])
# # def cashier():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         bill_amount = request.form['bill_amount']
# #         db = get_db()
# #         db.execute("UPDATE patients SET bill_amount = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (bill_amount, patient_id))
# #         db.commit()
# #         flash('Bill paid successfully!')
# #         return redirect(url_for('cashier'))
# #     return render_template('cashier.html')

# # # ---------------- Patient Detail ----------------
# # @app.route('/patient/<int:id>')
# # def patient_detail(id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
# #     return render_template('patient_detail.html', patient=patient)

# # # ---------------- Patient List ----------------
# # @app.route('/patients')
# # def patients():
# #     db = get_db()
# #     patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
# #     return render_template('patients.html', patients=patients)

# # # ---------------- Additional Sidebar Routes ----------------
# # @app.route('/admission')
# # def admission():
# #     return render_template('admission.html')

# # @app.route('/labor-delivery')
# # def labor_delivery():
# #     return render_template('labor_delivery.html')

# # @app.route('/appointments')
# # def appointments():
# #     db = get_db()
# #     appointments = db.execute("""
# #         SELECT a.*, 
# #                p.first_name || ' ' || p.last_name AS patient_name,
# #                d.first_name || ' ' || d.last_name AS doctor_name,
# #                strftime('%H:%M', a.appointment_date) AS time
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         JOIN doctors d ON a.doctor_id = d.id
# #         ORDER BY a.appointment_date ASC
# #     """).fetchall()
# #     return render_template('appointments.html', appointments=appointments)

# # @app.route('/medical-reports')
# # def medical_reports():
# #     return render_template('medical_reports.html')


# # @app.route('/search', methods=['GET', 'POST'])
# # def search():
# #     db = get_db()
# #     results = []

# #     if request.method == 'POST':
# #         query = request.form.get('query', '').strip()
# #         status = request.form.get('status', '').strip()
# #         date = request.form.get('date', '').strip()

# #         sql = "SELECT * FROM patients WHERE 1=1"
# #         params = []

# #         if query:
# #             sql += " AND (first_name LIKE ? OR last_name LIKE ? OR contact LIKE ? OR medical_record_number LIKE ?)"
# #             params += [f'%{query}%'] * 4
# #         if status:
# #             sql += " AND admission_status = ?"
# #             params.append(status)
# #         if date:
# #             sql += " AND DATE(created_at) = ?"
# #             params.append(date)

# #         results = db.execute(sql + " ORDER BY created_at DESC", params).fetchall()

# #     return render_template('search.html', results=results)

#     #     cursor = db.execute("""
#     #         INSERT INTO patients (
#     #             medical_record_number, first_name, last_name, age, gender, contact, address,
#     #             is_active, created_at, updated_at
#     #         ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#     #     """, (
#     #         mrn,
#     #         data['first_name'],
#     #         data['last_name'],
#     #         age,
#     #         data['gender'],
#     #         data['contact'],
#     #         data['address']
#     #     ))
#     #     db.commit()
#     #     new_id = cursor.lastrowid

#     #     # Optional: Send SMS
#     #     # sms.send("Welcome to Wauguzi Hospital. Your MRN is " + mrn, [data['contact']])

#     #     flash('Patient registered successfully!')
#     #     return redirect(url_for('patient_detail', id=new_id))

#     # return render_template('register.html')

# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         data = request.form
# #         db = get_db()
# #         db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             data['medical_record_number'], data['first_name'], data['last_name'],
# #             data['age'], data['gender'], data['contact'], data['address']
# #         ))
# #         db.commit()
# #         flash('Patient registered successfully!')
# #         return redirect(url_for('register'))
# #     return render_template('register.html')




# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3
# # from datetime import datetime

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

# # def get_db():
# #     conn = sqlite3.connect('hospital.db')
# #     conn.row_factory = sqlite3.Row
# #     return conn

# # # ---------------- Dashboard ----------------
# # @app.route('/')
# # def dashboard():
# #     db = get_db()
# #     today_sql = datetime.now().strftime('%Y-%m-%d')
# #     today_display = datetime.now().strftime('%A, %B %d, %Y')

# #     stats = {
# #         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
# #         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
# #         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today_sql,)).fetchone()[0],
# #         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
# #         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today_sql,)).fetchone()[0],
# #         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
# #         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
# #         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
# #         'efficiency': 0  # You can calculate this based on completed vs total appointments
# #     }

# #     return render_template('dashboard.html', stats=stats, current_date=today_display)

# # # ---------------- Patient Registration ----------------
# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         data = request.form
# #         db = get_db()
# #         db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             data['medical_record_number'], data['first_name'], data['last_name'],
# #             data['age'], data['gender'], data['contact'], data['address']
# #         ))
# #         db.commit()
# #         flash('Patient registered successfully!')
# #         return redirect(url_for('register'))
# #     return render_template('register.html')

# # # ---------------- Doctor Interface ----------------
# # @app.route('/doctor', methods=['GET', 'POST'])
# # def doctor():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
# #         db = get_db()
# #         db.execute("UPDATE patients SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (symptoms, diagnosis, patient_id))
# #         db.commit()
# #         flash('Diagnosis saved successfully!')
# #         return redirect(url_for('doctor'))
# #     return render_template('doctor.html')

# # # ---------------- Lab Results ----------------
# # @app.route('/lab', methods=['GET', 'POST'])
# # def lab():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         lab_results = request.form['lab_results']
# #         db = get_db()
# #         db.execute("UPDATE patients SET lab_results = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (lab_results, patient_id))
# #         db.commit()
# #         flash('Lab results saved successfully!')
# #         return redirect(url_for('lab'))
# #     return render_template('lab.html')

# # # ---------------- Pharmacy ----------------
# # @app.route('/pharmacist', methods=['GET', 'POST'])
# # def pharmacist():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         prescribed_medicine = request.form['prescribed_medicine']
# #         db = get_db()
# #         db.execute("UPDATE patients SET prescribed_medicine = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (prescribed_medicine, patient_id))
# #         db.commit()
# #         flash('Prescribed medicine saved successfully!')
# #         return redirect(url_for('pharmacist'))
# #     return render_template('pharmacist.html')

# # # ---------------- Billing ----------------
# # @app.route('/cashier', methods=['GET', 'POST'])
# # def cashier():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         bill_amount = request.form['bill_amount']
# #         db = get_db()
# #         db.execute("UPDATE patients SET bill_amount = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (bill_amount, patient_id))
# #         db.commit()
# #         flash('Bill paid successfully!')
# #         return redirect(url_for('cashier'))
# #     return render_template('cashier.html')

# # # ---------------- Patient Detail ----------------
# # @app.route('/patient/<int:id>')
# # def patient_detail(id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
# #     return render_template('patient_detail.html', patient=patient)

# # # ---------------- Patient List ----------------
# # @app.route('/patients')
# # def patients():
# #     db = get_db()
# #     patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
# #     return render_template('patients.html', patients=patients)

# # if __name__ == '__main__':
# #     app.run(debug=True)


# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3
# # from datetime import datetime

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

# # def get_db():
# #     conn = sqlite3.connect('hospital.db')
# #     conn.row_factory = sqlite3.Row
# #     return conn

# # # ---------------- Dashboard ----------------
# # @app.route('/')
# # def dashboard():
# #     db = get_db()
# #     today = datetime.now().strftime('%Y-%m-%d')
# #     display_date = datetime.now().strftime('%A, %B %d, %Y')

# #     stats = {
# #         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
# #         'total_doctors': db.execute("SELECT COUNT(*) FROM doctors WHERE is_active = 1").fetchone()[0],
# #         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today,)).fetchone()[0],
# #         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
# #         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today,)).fetchone()[0],
# #         'admitted_patients': db.execute("SELECT COUNT(*) FROM patients WHERE admission_status = 'admitted'").fetchone()[0],
# #         'in_labor': db.execute("SELECT COUNT(*) FROM patients WHERE labor_status = 'active'").fetchone()[0],
# #         'available_beds': db.execute("SELECT COUNT(*) FROM beds WHERE status = 'available'").fetchone()[0],
# #         'efficiency': 0  # You can calculate this later
# #     }

# #     appointments = db.execute("""
# #         SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name,
# #                d.first_name || ' ' || d.last_name AS doctor_name
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         JOIN doctors d ON a.doctor_id = d.id
# #         WHERE DATE(a.appointment_date) = ?
# #         ORDER BY a.appointment_date ASC
# #     """, (today,)).fetchall()

# #     return render_template('dashboard.html', stats=stats, appointments=appointments, current_date=display_date)

# # # ---------------- Sidebar Routes ----------------
# # @app.route('/check-in')
# # def check_in():
# #     return render_template('check_in.html')

# # @app.route('/doctor-interface')
# # def doctor_interface():
# #     return render_template('doctor_interface.html')

# # @app.route('/laboratory')
# # def laboratory():
# #     return render_template('laboratory.html')

# # @app.route('/pharmacy')
# # def pharmacy():
# #     return render_template('pharmacy.html')

# # @app.route('/billing')
# # def billing():
# #     return render_template('billing.html')

# # @app.route('/patients')
# # def patients():
# #     db = get_db()
# #     patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
# #     return render_template('patients.html', patients=patients)

# # @app.route('/admission')
# # def admission():
# #     return render_template('admission.html')

# # @app.route('/labor-delivery')
# # def labor_delivery():
# #     return render_template('labor_delivery.html')

# # @app.route('/appointments')
# # def appointments():
# #     db = get_db()
# #     appointments = db.execute("""
# #         SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name,
# #                d.first_name || ' ' || d.last_name AS doctor_name
# #         FROM appointments a
# #         JOIN patients p ON a.patient_id = p.id
# #         JOIN doctors d ON a.doctor_id = d.id
# #         ORDER BY a.appointment_date ASC
# #     """).fetchall()
# #     return render_template('appointments.html', appointments=appointments)

# # @app.route('/medical-reports')
# # def medical_reports():
# #     return render_template('medical_reports.html')

# # if __name__ == '__main__':
# #     app.run(debug=True)

# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3
# # from datetime import datetime

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

# # def get_db():
# #     conn = sqlite3.connect('hospital.db')
# #     conn.row_factory = sqlite3.Row
# #     return conn

# # # ---------------- Dashboard ----------------
# # @app.route('/')
# # def dashboard():
# #     db = get_db()
# #     today = datetime.now().strftime('%Y-%m-%d')
# #     stats = {
# #         'total_patients': db.execute("SELECT COUNT(*) FROM patients WHERE is_active = 1").fetchone()[0],
# #         'today_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ?", (today,)).fetchone()[0],
# #         'pending_appointments': db.execute("SELECT COUNT(*) FROM appointments WHERE status IN ('scheduled', 'confirmed')").fetchone()[0],
# #         'completed_appointments_today': db.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = ? AND status = 'completed'", (today,)).fetchone()[0]
# #     }
# #     return render_template('dashboard.html', stats=stats)

# # # ---------------- Patient Registration ----------------
# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
# #     if request.method == 'POST':
# #         data = request.form
# #         db = get_db()
# #         db.execute("""
# #             INSERT INTO patients (
# #                 medical_record_number, first_name, last_name, age, gender, contact, address,
# #                 is_active, created_at, updated_at
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
# #         """, (
# #             data['medical_record_number'], data['first_name'], data['last_name'],
# #             data['age'], data['gender'], data['contact'], data['address']
# #         ))
# #         db.commit()
# #         flash('Patient registered successfully!')
# #         return redirect(url_for('register'))
# #     return render_template('register.html')

# # # ---------------- Doctor Interface ----------------
# # @app.route('/doctor', methods=['GET', 'POST'])
# # def doctor():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         symptoms = request.form['symptoms']
# #         diagnosis = request.form['diagnosis']
# #         db = get_db()
# #         db.execute("UPDATE patients SET symptoms = ?, diagnosis = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (symptoms, diagnosis, patient_id))
# #         db.commit()
# #         flash('Diagnosis saved successfully!')
# #         return redirect(url_for('doctor'))
# #     return render_template('doctor.html')

# # # ---------------- Lab Results ----------------
# # @app.route('/lab', methods=['GET', 'POST'])
# # def lab():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         lab_results = request.form['lab_results']
# #         db = get_db()
# #         db.execute("UPDATE patients SET lab_results = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (lab_results, patient_id))
# #         db.commit()
# #         flash('Lab results saved successfully!')
# #         return redirect(url_for('lab'))
# #     return render_template('lab.html')

# # # ---------------- Pharmacy ----------------
# # @app.route('/pharmacist', methods=['GET', 'POST'])
# # def pharmacist():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         prescribed_medicine = request.form['prescribed_medicine']
# #         db = get_db()
# #         db.execute("UPDATE patients SET prescribed_medicine = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (prescribed_medicine, patient_id))
# #         db.commit()
# #         flash('Prescribed medicine saved successfully!')
# #         return redirect(url_for('pharmacist'))
# #     return render_template('pharmacist.html')

# # # ---------------- Billing ----------------
# # @app.route('/cashier', methods=['GET', 'POST'])
# # def cashier():
# #     if request.method == 'POST':
# #         patient_id = request.form['patient_id']
# #         bill_amount = request.form['bill_amount']
# #         db = get_db()
# #         db.execute("UPDATE patients SET bill_amount = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
# #                    (bill_amount, patient_id))
# #         db.commit()
# #         flash('Bill paid successfully!')
# #         return redirect(url_for('cashier'))
# #     return render_template('cashier.html')

# # # ---------------- Patient Detail ----------------
# # @app.route('/patient/<int:id>')
# # def patient_detail(id):
# #     db = get_db()
# #     patient = db.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
# #     return render_template('patient_detail.html', patient=patient)

# # # ---------------- Patient List ----------------
# # @app.route('/patients')
# # def patients():
# #     db = get_db()
# #     patients = db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
# #     return render_template('patients.html', patients=patients)

# # if __name__ == '__main__':
# #     app.run(debug=True)












# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

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
# #     app.run(debug=True, port=5001)


# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

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
# #     app.run(debug=True, port=5001)





# # from flask import Flask, render_template, request, redirect, url_for, flash
# # import sqlite3

# # app = Flask(__name__)
# # app.secret_key = 'supersecretkey'

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
# #     app.run(debug=True, port=5001)






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
# #     app.run(debug=True, port=5001)









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
# #     app.run(debug=True, port=5001)

# # if __name__ == '__main__':
# #     app.run(debug=True)




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

# # # Home Route (Modified to pass patients)
# # @app.route('/')
# # @app.route('/')
# # def home():
# #     conn = connect_db()
# #     cursor = conn.cursor()
# #     cursor.execute('SELECT * FROM patients')
# #     patients = cursor.fetchall()
# #     conn.close()
# #     return render_template('index.html', patients=patients)

# # # def home():
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT id, name FROM patients')  # Fetch patient IDs and names
# # #     patients = cursor.fetchall()
# # #     conn.close()
# # #     return render_template('index.html', patients=patients)

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

# # # @app.route('/doctor/<int:id>', methods=['GET', 'POST'])
# # # def doctor(id):
# # #     # conn = connect_db()
# # #     # cursor = conn.cursor()
# # #     # cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# # #     # patient = cursor.fetchone()


# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM patients')
# # #     patients = cursor.fetchall()
# # #     conn.close()

# # #     if request.method == 'POST':
# # #         symptoms = request.form['symptoms']
# # #         diagnosis = request.form['diagnosis']
        
# # #         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?', 
# # #                        (symptoms, diagnosis, id))
# # #         conn.commit()
# # #         conn.close()

# # #         flash('Patient diagnosis updated!')
# # #         return redirect(url_for('doctor', id=id))

# # #     conn.close()
# # #     return render_template('doctor.html', patient=patient)

# # # Lab: Enter lab results

# # # @app.route('/lab/<int:id>', methods=['GET'])
# # # def lab(id):
# # #     # Example logic to handle the lab request
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM lab_tests WHERE patient_id = ?', (id,))
# # #     lab_test = cursor.fetchone()
# # #     conn.close()
# # #     return render_template('lab.html', lab_test=lab_test)

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






# # # from flask import Flask, render_template, request, redirect, url_for, flash
# # # import sqlite3

# # # app = Flask(__name__)
# # # app.secret_key = 'supersecretkey'  # For flash messages

# # # # Database connection
# # # def connect_db():
# # #     return sqlite3.connect('hospital.db')

# # # # Create tables (do this once to set up your database)
# # # def init_db():
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('''
# # #         CREATE TABLE IF NOT EXISTS patients (
# # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #             name TEXT,
# # #             age INTEGER,
# # #             gender TEXT,
# # #             contact TEXT,
# # #             address TEXT,
# # #             symptoms TEXT,
# # #             diagnosis TEXT,
# # #             lab_results TEXT,
# # #             prescribed_medicine TEXT,
# # #             bill_amount REAL
# # #         )
# # #     ''')
# # #     conn.commit()
# # #     conn.close()

# # # # Home Route
# # # @app.route('/')
# # # def home():
# # #     return render_template('index.html')

# # # # Reception: Register a patient
# # # @app.route('/register', methods=['GET', 'POST'])
# # # def register():
# # #     if request.method == 'POST':
# # #         name = request.form['name']
# # #         age = request.form['age']
# # #         gender = request.form['gender']
# # #         contact = request.form['contact']
# # #         address = request.form['address']

# # #         conn = connect_db()
# # #         cursor = conn.cursor()
# # #         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)', 
# # #                        (name, age, gender, contact, address))
# # #         conn.commit()
# # #         conn.close()

# # #         flash('Patient registered successfully!')
# # #         return redirect(url_for('home'))
# # #     return render_template('register.html')

# # # # Doctor: View and update patient details
# # # @app.route('/doctor/<int:id>', methods=['GET', 'POST'])
# # # def doctor(id):
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# # #     patient = cursor.fetchone()

# # #     if request.method == 'POST':
# # #         symptoms = request.form['symptoms']
# # #         diagnosis = request.form['diagnosis']
        
# # #         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?', 
# # #                        (symptoms, diagnosis, id))
# # #         conn.commit()
# # #         conn.close()

# # #         flash('Patient diagnosis updated!')
# # #         return redirect(url_for('doctor', id=id))

# # #     conn.close()
# # #     return render_template('doctor.html', patient=patient)

# # # # Lab: Enter lab results
# # # @app.route('/lab/<int:id>', methods=['GET', 'POST'])
# # # def lab(id):
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# # #     patient = cursor.fetchone()

# # #     if request.method == 'POST':
# # #         lab_results = request.form['lab_results']
# # #         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?', (lab_results, id))
# # #         conn.commit()
# # #         conn.close()

# # #         flash('Lab results updated!')
# # #         return redirect(url_for('doctor', id=id))

# # #     conn.close()
# # #     return render_template('lab.html', patient=patient)

# # # # Pharmacist: Dispense medicines
# # # @app.route('/pharmacist/<int:id>', methods=['GET', 'POST'])
# # # def pharmacist(id):
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# # #     patient = cursor.fetchone()

# # #     if request.method == 'POST':
# # #         prescribed_medicine = request.form['prescribed_medicine']
# # #         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?', 
# # #                        (prescribed_medicine, id))
# # #         conn.commit()
# # #         conn.close()

# # #         flash('Medicine prescribed!')
# # #         return redirect(url_for('doctor', id=id))

# # #     conn.close()
# # #     return render_template('pharmacist.html', patient=patient)

# # # # Cashier: Handle billing
# # # @app.route('/cashier/<int:id>', methods=['GET', 'POST'])
# # # def cashier(id):
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# # #     patient = cursor.fetchone()

# # #     if request.method == 'POST':
# # #         bill_amount = request.form['bill_amount']
# # #         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?', (bill_amount, id))
# # #         conn.commit()
# # #         conn.close()

# # #         flash('Bill payment recorded!')
# # #         return redirect(url_for('home'))

# # #     conn.close()
# # #     return render_template('cashier.html', patient=patient)

# # # # Display patient details
# # # @app.route('/patient/<int:id>')
# # # def patient_detail(id):
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# # #     patient = cursor.fetchone()
# # #     conn.close()
# # #     return render_template('patient_detail.html', patient=patient)

# # # if __name__ == '__main__':
# # #     init_db()
# # #     app.run(debug=True)







# # # from flask import Flask, render_template, request, redirect, url_for, flash
# # # import sqlite3

# # # app = Flask(__name__)
# # # app.secret_key = 'supersecretkey'  # Necessary for flash messages

# # # def connect_db():
# # #     return sqlite3.connect('hospital.db')

# # # @app.route('/')
# # # def home():
# # #     return render_template('index.html')

# # # @app.route('/register', methods=['GET', 'POST'])
# # # def register():
# # #     if request.method == 'POST':
# # #         name = request.form['name']
# # #         age = request.form['age']
# # #         gender = request.form['gender']
# # #         contact = request.form['contact']
# # #         address = request.form['address']
        
# # #         conn = connect_db()
# # #         cursor = conn.cursor()
# # #         cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
# # #                        (name, age, gender, contact, address))
# # #         conn.commit()
# # #         conn.close()
        
# # #         flash('Patient registered successfully!')
# # #         return redirect(url_for('home'))
# # #     return render_template('register.html')

# # # @app.route('/doctor', methods=['GET', 'POST'])
# # # def doctor():
# # #     if request.method == 'POST':
# # #         patient_id = request.form['patient_id']
# # #         symptoms = request.form['symptoms']
# # #         diagnosis = request.form['diagnosis']
        
# # #         conn = connect_db()
# # #         cursor = conn.cursor()
# # #         cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
# # #                        (symptoms, diagnosis, patient_id))
# # #         conn.commit()
# # #         conn.close()
        
# # #         flash('Diagnosis saved successfully!')
# # #         return redirect(url_for('home'))
# # #     return render_template('doctor.html')

# # # @app.route('/lab', methods=['GET', 'POST'])
# # # def lab():
# # #     if request.method == 'POST':
# # #         patient_id = request.form['patient_id']
# # #         lab_results = request.form['lab_results']
        
# # #         conn = connect_db()
# # #         cursor = conn.cursor()
# # #         cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
# # #                        (lab_results, patient_id))
# # #         conn.commit()
# # #         conn.close()
        
# # #         flash('Lab results saved successfully!')
# # #         return redirect(url_for('home'))
# # #     return render_template('lab.html')

# # # @app.route('/pharmacist', methods=['GET', 'POST'])
# # # def pharmacist():
# # #     if request.method == 'POST':
# # #         patient_id = request.form['patient_id']
# # #         prescribed_medicine = request.form['prescribed_medicine']
        
# # #         conn = connect_db()
# # #         cursor = conn.cursor()
# # #         cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
# # #                        (prescribed_medicine, patient_id))
# # #         conn.commit()
# # #         conn.close()
        
# # #         flash('Prescribed medicine saved successfully!')
# # #         return redirect(url_for('home'))
# # #     return render_template('pharmacist.html')

# # # @app.route('/cashier', methods=['GET', 'POST'])
# # # def cashier():
# # #     if request.method == 'POST':
# # #         patient_id = request.form['patient_id']
# # #         bill_amount = request.form['bill_amount']
        
# # #         conn = connect_db()
# # #         cursor = conn.cursor()
# # #         cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
# # #                        (bill_amount, patient_id))
# # #         conn.commit()
# # #         conn.close()
        
# # #         flash('Bill paid successfully!')
# # #         return redirect(url_for('home'))
# # #     return render_template('cashier.html')

# # # @app.route('/patient/<int:id>')
# # # def patient_detail(id):
# # #     conn = connect_db()
# # #     cursor = conn.cursor()
# # #     cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
# # #     patient = cursor.fetchone()
# # #     conn.close()
# # #     return render_template('patient_detail.html', patient=patient)

# # # if __name__ == '__main__':
# # #     app.run(debug=True)







