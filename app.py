import os
import sqlite3
from flask import Flask, request, session, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import openpyxl
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.sqlite')

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            patient_name TEXT,
            email TEXT,
            phone TEXT,
            doctor TEXT,
            date TEXT,
            time TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS health_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            temperature REAL,
            bp_sys INTEGER,
            bp_dia INTEGER,
            heart_rate INTEGER,
            blood_sugar INTEGER,
            oxygen_level REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            specialty TEXT,
            specialty_name TEXT,
            clinic TEXT,
            rating REAL,
            experience TEXT,
            image TEXT
        )
    ''')
    
    # Seed doctors if table is empty
    cur = conn.execute('SELECT COUNT(*) as count FROM doctors')
    if cur.fetchone()['count'] == 0:
        docs = [
            ("Dr. Dhaval Pandya", "general", "General Physician", "Impulse Hospital & ICU", 4.9, "18 years", "dr.dhaval.webp"),
            ("Dr. Gopal Shah", "cardiology", "Cardiology", "Heart Care Hospital", 4.9, "20 years", "male_doctor.png"),
            ("Dr. Apoorva Shah", "pediatrics", "Pediatrics", "Children's Health Clinic", 4.7, "12 years", "male_doctor.png"),
            ("Dr. Dipak Patel", "dermatology", "Dermatology", "Skin Care Institute", 4.6, "10 years", "male_doctor.png"),
            ("Dr. Rajnikant Dave", "general", "General Physician", "Community Health Center", 4.8, "18 years", "male_doctor.png"),
            ("Dr. Payal Joshi", "cardiology", "Cardiology", "Advanced Cardiac Care", 4.9, "25 years", "female_doctor.png"),
            ("Dr. Kavita Patel", "pediatrics", "Pediatrics", "Kids First Medical", 4.8, "14 years", "female_doctor.png"),
            ("Dr. Rajesh Patel", "dermatology", "Dermatology", "Derma Wellness Center", 4.7, "16 years", "male_doctor.png")
        ]
        conn.executemany('INSERT INTO doctors (name, specialty, specialty_name, clinic, rating, experience, image) VALUES (?, ?, ?, ?, ?, ?, ?)', docs)
    
    conn.commit()
    conn.close()


def export_to_excel():
    """Export users and appointments tables to data.xlsx in the project root."""
    wb_path = os.path.join(BASE_DIR, 'data.xlsx')
    conn = get_db()
    try:
        users = conn.execute('SELECT id, username, email FROM users ORDER BY id').fetchall()
        appts = conn.execute('SELECT id, user_id, patient_name, email, phone, doctor, date, time, reason, created_at FROM appointments ORDER BY created_at DESC').fetchall()
        health = conn.execute('SELECT id, user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at FROM health_data ORDER BY created_at DESC').fetchall()
    finally:
        conn.close()

    # Load or create workbook
    if os.path.exists(wb_path):
        wb = openpyxl.load_workbook(wb_path)
    else:
        wb = openpyxl.Workbook()

    # Remove default sheet if it's the only sheet
    if 'Sheet' in wb.sheetnames and len(wb.sheetnames) == 1:
        wb.remove(wb['Sheet'])

    # Replace or create users sheet
    if 'users' in wb.sheetnames:
        del wb['users']
    ws = wb.create_sheet('users')
    ws.append(['id', 'username', 'email'])
    for r in users:
        ws.append([r['id'], r['username'], r['email']])

    # Replace or create appointments sheet
    if 'appointments' in wb.sheetnames:
        del wb['appointments']
    ws2 = wb.create_sheet('appointments')
    ws2.append(['id', 'user_id', 'patient_name', 'email', 'phone', 'doctor', 'date', 'time', 'reason', 'created_at'])
    for a in appts:
        ws2.append([a['id'], a['user_id'], a['patient_name'], a['email'], a['phone'], a['doctor'], a['date'], a['time'], a['reason'], a['created_at']])

    # Replace or create health_data sheet
    if 'health_data' in wb.sheetnames:
        del wb['health_data']
    ws3 = wb.create_sheet('health_data')
    ws3.append(['id', 'user_id', 'temperature', 'bp_sys', 'bp_dia', 'heart_rate', 'blood_sugar', 'oxygen_level', 'created_at'])
    for h in health:
        ws3.append([h['id'], h['user_id'], h['temperature'], h['bp_sys'], h['bp_dia'], h['heart_rate'], h['blood_sugar'], h['oxygen_level'], h['created_at']])

    # Replace or create doctors sheet
    if 'doctors' in wb.sheetnames:
        del wb['doctors']
    ws4 = wb.create_sheet('doctors')
    ws4.append(['id', 'name', 'specialty', 'specialty_name', 'clinic', 'rating', 'experience', 'image'])
    conn = get_db()
    try:
        doctors = conn.execute('SELECT id, name, specialty, specialty_name, clinic, rating, experience, image FROM doctors').fetchall()
        for d in doctors:
            ws4.append([d['id'], d['name'], d['specialty'], d['specialty_name'], d['clinic'], d['rating'], d['experience'], d['image']])
    finally:
        conn.close()

    wb.save(wb_path)

def export_csvs():
    """Write users.csv and appointments.csv to project root."""
    import csv
    conn = get_db()
    try:
        users = conn.execute('SELECT id, username, email FROM users ORDER BY id').fetchall()
        appts = conn.execute('SELECT id, user_id, patient_name, email, phone, doctor, date, time, reason, created_at FROM appointments ORDER BY created_at DESC').fetchall()
        health = conn.execute('SELECT id, user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at FROM health_data ORDER BY created_at DESC').fetchall()
    finally:
        conn.close()

    users_path = os.path.join(BASE_DIR, 'users.csv')
    appts_path = os.path.join(BASE_DIR, 'appointments.csv')
    health_path = os.path.join(BASE_DIR, 'health_data.csv')

    with open(users_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'username', 'email'])
        for u in users:
            writer.writerow([u['id'], u['username'], u['email']])

    with open(appts_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'user_id', 'patient_name', 'email', 'phone', 'doctor', 'date', 'time', 'reason', 'created_at'])
        for a in appts:
            writer.writerow([a['id'], a['user_id'], a['patient_name'], a['email'], a['phone'], a['doctor'], a['date'], a['time'], a['reason'], a['created_at']])

    with open(health_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'user_id', 'temperature', 'bp_sys', 'bp_dia', 'heart_rate', 'blood_sugar', 'oxygen_level', 'created_at'])
        for h in health:
            writer.writerow([h['id'], h['user_id'], h['temperature'], h['bp_sys'], h['bp_dia'], h['heart_rate'], h['blood_sugar'], h['oxygen_level'], h['created_at']])

    # Export doctors.csv
    doctors_path = os.path.join(BASE_DIR, 'doctors.csv')
    conn = get_db()
    try:
        docs = conn.execute('SELECT id, name, specialty, specialty_name, clinic, rating, experience, image FROM doctors').fetchall()
    finally:
        conn.close()
        
    with open(doctors_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'specialty', 'specialty_name', 'clinic', 'rating', 'experience', 'image'])
        for d in docs:
            writer.writerow([d['id'], d['name'], d['specialty'], d['specialty_name'], d['clinic'], d['rating'], d['experience'], d['image']])



init_db()

def find_user_by_identifier(identifier):
    conn = get_db()
    cur = conn.execute('SELECT id, username, email, password FROM users WHERE email = ? OR username = ?', (identifier, identifier))
    row = cur.fetchone()
    conn.close()
    return row

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password')  # Ensure password is retrieved
    if not username or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400

    conn = get_db()
    try:
        cur = conn.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cur.fetchone():
            return jsonify({'error': 'Email already registered'}), 409

        pwd_hash = generate_password_hash(password)
        cur = conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, pwd_hash))
        conn.commit()
        user_id = cur.lastrowid
        session['user_id'] = user_id
        # update excel export
        try:
            export_to_excel()
            export_csvs()
        except Exception:
            pass
        return jsonify({'id': user_id, 'username': username, 'email': email}), 201
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = (data.get('identifier') or '').strip()
    password = data.get('password')
    if not identifier or not password:
        return jsonify({'error': 'Missing fields'}), 400

    row = find_user_by_identifier(identifier)
    if not row:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not check_password_hash(row['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = row['id']
    return jsonify({'id': row['id'], 'username': row['username'], 'email': row['email']})

@app.route('/api/me')
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    conn = get_db()
    cur = conn.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': row['id'], 'username': row['username'], 'email': row['email']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})


@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    patient_name = data.get('patient_name')
    email = data.get('email')
    phone = data.get('phone')
    doctor = data.get('doctor')
    date = data.get('date')
    time = data.get('time')
    reason = data.get('reason')

    if not (patient_name and email and doctor and date and time):
        return jsonify({'error': 'Missing fields'}), 400

    try:
        conn = get_db()
        cur = conn.execute(
            'INSERT INTO appointments (user_id, patient_name, email, phone, doctor, date, time, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, patient_name, email, phone, doctor, date, time, reason)
        )
        conn.commit()
        appt_id = cur.lastrowid
        cur = conn.execute('SELECT id, patient_name, email, phone, doctor, date, time, reason, created_at FROM appointments WHERE id = ?', (appt_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            # update excel export
            try:
                export_to_excel()
                export_csvs()
            except Exception:
                pass
            return jsonify(dict(row)), 201
        return jsonify({'error': 'Failed to create appointment'}), 500
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/appointments', methods=['GET'])
def list_appointments():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        conn = get_db()
        cur = conn.execute('SELECT id, patient_name, email, phone, doctor, date, time, reason, created_at FROM appointments WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        rows = cur.fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/appointments/<int:appt_id>', methods=['DELETE'])
def delete_appointment(appt_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        conn = get_db()
        cur = conn.execute('SELECT user_id FROM appointments WHERE id = ?', (appt_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Appointment not found'}), 404
        if row['user_id'] != user_id:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403

        conn.execute('DELETE FROM appointments WHERE id = ?', (appt_id,))
        conn.commit()
        conn.close()
        try:
            export_to_excel()
            export_csvs()
        except Exception:
            pass
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/health', methods=['POST'])
def save_health_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json() or {}
    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO health_data (user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, data.get('temperature'), data.get('bp_sys'), data.get('bp_dia'), data.get('heart_rate'), data.get('blood_sugar'), data.get('oxygen_level'))
        )
        conn.commit()
        conn.close()
        try:
            export_to_excel()
            export_csvs()
        except Exception:
            pass
        return jsonify({'ok': True}), 201
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/health', methods=['GET'])
def get_health_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db()
        cur = conn.execute('SELECT id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at as timestamp FROM health_data WHERE user_id = ? ORDER BY created_at ASC', (user_id,))
        rows = cur.fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/doctors', methods=['GET'])
def list_doctors():
    try:
        conn = get_db()
        cur = conn.execute('SELECT id, name, specialty, specialty_name, clinic, rating, experience, image FROM doctors')
        rows = cur.fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({
            'text': "I'm sorry, my AI features are currently not configured. Please ask the administrator to configure the Gemini API key.",
            'action': None
        })
        
    try:
        conn = get_db()
        docs = conn.execute('SELECT name, specialty_name FROM doctors').fetchall()
        conn.close()
        doctor_list = "\n".join([f"- {d['name']} ({d['specialty_name']})" for d in docs])
        
        client = genai.Client(api_key=api_key)
        
        system_prompt = f"""You are a helpful, empathetic healthcare assistant for Smart Healthcare.
You help users with general health advice, finding doctors, and booking appointments.
Our available doctors are:
{doctor_list}

Always be polite and empathetic. If the user asks about booking an appointment, recommend the appropriate specialty or doctor, and ask if they would like to view doctors or book an appointment.
DO NOT provide definitive medical diagnoses, always recommend seeing a doctor for serious conditions. Provide practical, standard advice for common mild symptoms (e.g., rest, hydration).
Keep your responses concise and well-formatted."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=400,
            ),
        )
        
        reply = response.text
        
        # Suggest actions based on context
        action = None
        lower_reply = reply.lower() if reply else ""
        if "book" in lower_reply or "appointment" in lower_reply:
            action = "appointments"
        elif "doctor" in lower_reply or "specialist" in lower_reply or "physician" in lower_reply:
            action = "doctors"
            
        return jsonify({'text': reply, 'action': action})
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': 'Failed to process chat message'}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def static_proxy(path):
    if path.startswith('api'):
        return jsonify({'error': 'Not found'}), 404
    if path == '' or not os.path.exists(os.path.join(BASE_DIR, path)):
        return send_from_directory(BASE_DIR, 'index.html')
    return send_from_directory(BASE_DIR, path)


@app.route('/download/data.xlsx')
def download_excel():
    wb_path = os.path.join(BASE_DIR, 'data.xlsx')
    if not os.path.exists(wb_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(wb_path, as_attachment=True, download_name='data.xlsx')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)), debug=True)
