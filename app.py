from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necessary for flash messages

def connect_db():
    return sqlite3.connect('hospital.db')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']
        address = request.form['address']
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO patients (name, age, gender, contact, address) VALUES (?, ?, ?, ?, ?)',
                       (name, age, gender, contact, address))
        conn.commit()
        conn.close()
        
        flash('Patient registered successfully!')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        symptoms = request.form['symptoms']
        diagnosis = request.form['diagnosis']
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE patients SET symptoms = ?, diagnosis = ? WHERE id = ?',
                       (symptoms, diagnosis, patient_id))
        conn.commit()
        conn.close()
        
        flash('Diagnosis saved successfully!')
        return redirect(url_for('home'))
    return render_template('doctor.html')

@app.route('/lab', methods=['GET', 'POST'])
def lab():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        lab_results = request.form['lab_results']
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE patients SET lab_results = ? WHERE id = ?',
                       (lab_results, patient_id))
        conn.commit()
        conn.close()
        
        flash('Lab results saved successfully!')
        return redirect(url_for('home'))
    return render_template('lab.html')

@app.route('/pharmacist', methods=['GET', 'POST'])
def pharmacist():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        prescribed_medicine = request.form['prescribed_medicine']
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE patients SET prescribed_medicine = ? WHERE id = ?',
                       (prescribed_medicine, patient_id))
        conn.commit()
        conn.close()
        
        flash('Prescribed medicine saved successfully!')
        return redirect(url_for('home'))
    return render_template('pharmacist.html')

@app.route('/cashier', methods=['GET', 'POST'])
def cashier():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        bill_amount = request.form['bill_amount']
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE patients SET bill_amount = ? WHERE id = ?',
                       (bill_amount, patient_id))
        conn.commit()
        conn.close()
        
        flash('Bill paid successfully!')
        return redirect(url_for('home'))
    return render_template('cashier.html')

@app.route('/patient/<int:id>')
def patient_detail(id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients WHERE id = ?', (id,))
    patient = cursor.fetchone()
    conn.close()
    return render_template('patient_detail.html', patient=patient)

if __name__ == '__main__':
    app.run(debug=True)
