import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import openpyxl
from dotenv import load_dotenv
from google import genai
from google.genai import types
...
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise Exception("DATABASE_URL not set")

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode='require',
        cursor_factory=RealDictCursor
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            gender TEXT,
            blood_group TEXT,
            phone TEXT,
            address TEXT,
            medical_history TEXT
        )
    ''')
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS blood_group TEXT;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS medical_history TEXT;")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            patient_name TEXT,
            email TEXT,
            phone TEXT,
            doctor TEXT,
            date TEXT,
            time TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            cancel_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    cur.execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Pending';")
    cur.execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS cancel_reason TEXT;")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS health_data (
            id SERIAL PRIMARY KEY,
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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            specialty TEXT,
            specialty_name TEXT,
            clinic TEXT,
            rating REAL,
            experience TEXT,
            image TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    cur.execute("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS email TEXT UNIQUE;")
    cur.execute("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS password TEXT;")
    
    # Seed doctors if table is empty
    cur.execute('SELECT COUNT(*) as count FROM doctors')
    if cur.fetchone()['count'] == 0:
        default_pw = generate_password_hash('password123')
        docs = [
            ("Dr. Dhaval Pandya", "general", "General Physician", "Impulse Hospital & ICU", 4.9, "18 years", "dr.dhaval.webp", "dhaval@example.com", default_pw),
            ("Dr. Gopal Shah", "cardiology", "Cardiology", "Heart Care Hospital", 4.9, "20 years", "male_doctor.png", "gopal@example.com", default_pw),
            ("Dr. Apoorva Shah", "pediatrics", "Pediatrics", "Children's Health Clinic", 4.7, "12 years", "male_doctor.png", "apoorva@example.com", default_pw),
            ("Dr. Dipak Patel", "dermatology", "Dermatology", "Skin Care Institute", 4.6, "10 years", "male_doctor.png", "dipak@example.com", default_pw),
            ("Dr. Rajnikant Dave", "general", "General Physician", "Community Health Center", 4.8, "18 years", "male_doctor.png", "rajnikant@example.com", default_pw),
            ("Dr. Payal Joshi", "cardiology", "Cardiology", "Advanced Cardiac Care", 4.9, "25 years", "female_doctor.png", "payal@example.com", default_pw),
            ("Dr. Kavita Patel", "pediatrics", "Pediatrics", "Kids First Medical", 4.8, "14 years", "female_doctor.png", "kavita@example.com", default_pw),
            ("Dr. Rajesh Patel", "dermatology", "Dermatology", "Derma Wellness Center", 4.7, "16 years", "male_doctor.png", "rajesh@example.com", default_pw)
        ]
        cur.executemany('INSERT INTO doctors (name, specialty, specialty_name, clinic, rating, experience, image, email, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', docs)
    else:
        # Give existing doctors a default password if missing
        cur.execute("UPDATE doctors SET email = REPLACE(LOWER(name), ' ', '') || '@example.com', password = %s WHERE email IS NULL", (generate_password_hash('password123'),))
    
    conn.commit()
    cur.close()
    conn.close()


def export_to_excel():
    """Export users and appointments tables to data.xlsx in the project root."""
    wb_path = os.path.join(BASE_DIR, 'data.xlsx')
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, username, email FROM users ORDER BY id')
        users = cur.fetchall()
        cur.execute('SELECT id, user_id, patient_name, email, phone, doctor, date, time, reason, status, cancel_reason, created_at FROM appointments ORDER BY created_at DESC')
        appts = cur.fetchall()
        cur.execute('SELECT id, user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at FROM health_data ORDER BY created_at DESC')
        health = cur.fetchall()
    finally:
        cur.close()
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
    ws2.append(['id', 'user_id', 'patient_name', 'email', 'phone', 'doctor', 'date', 'time', 'reason', 'status', 'cancel_reason', 'created_at'])
    for a in appts:
        # created_at might be datetime object from psycopg2, convert to string
        created_at_str = str(a['created_at']) if a['created_at'] else ''
        ws2.append([a['id'], a['user_id'], a['patient_name'], a['email'], a['phone'], a['doctor'], a['date'], a['time'], a['reason'], a['status'], a['cancel_reason'], created_at_str])

    # Replace or create health_data sheet
    if 'health_data' in wb.sheetnames:
        del wb['health_data']
    ws3 = wb.create_sheet('health_data')
    ws3.append(['id', 'user_id', 'temperature', 'bp_sys', 'bp_dia', 'heart_rate', 'blood_sugar', 'oxygen_level', 'created_at'])
    for h in health:
        created_at_str = str(h['created_at']) if h['created_at'] else ''
        ws3.append([h['id'], h['user_id'], h['temperature'], h['bp_sys'], h['bp_dia'], h['heart_rate'], h['blood_sugar'], h['oxygen_level'], created_at_str])

    # Replace or create doctors sheet
    if 'doctors' in wb.sheetnames:
        del wb['doctors']
    ws4 = wb.create_sheet('doctors')
    ws4.append(['id', 'name', 'specialty', 'specialty_name', 'clinic', 'rating', 'experience', 'image'])
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, name, specialty, specialty_name, clinic, rating, experience, image FROM doctors')
        doctors = cur.fetchall()
        for d in doctors:
            ws4.append([d['id'], d['name'], d['specialty'], d['specialty_name'], d['clinic'], d['rating'], d['experience'], d['image']])
    finally:
        cur.close()
        conn.close()

    wb.save(wb_path)

def export_csvs():
    """Write users.csv and appointments.csv to project root."""
    import csv
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, username, email FROM users ORDER BY id')
        users = cur.fetchall()
        cur.execute('SELECT id, user_id, patient_name, email, phone, doctor, date, time, reason, status, cancel_reason, created_at FROM appointments ORDER BY created_at DESC')
        appts = cur.fetchall()
        cur.execute('SELECT id, user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at FROM health_data ORDER BY created_at DESC')
        health = cur.fetchall()
    finally:
        cur.close()
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
        writer.writerow(['id', 'user_id', 'patient_name', 'email', 'phone', 'doctor', 'date', 'time', 'reason', 'status', 'cancel_reason', 'created_at'])
        for a in appts:
            created_at_str = str(a['created_at']) if a['created_at'] else ''
            writer.writerow([a['id'], a['user_id'], a['patient_name'], a['email'], a['phone'], a['doctor'], a['date'], a['time'], a['reason'], a['status'], a['cancel_reason'], created_at_str])

    with open(health_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'user_id', 'temperature', 'bp_sys', 'bp_dia', 'heart_rate', 'blood_sugar', 'oxygen_level', 'created_at'])
        for h in health:
            created_at_str = str(h['created_at']) if h['created_at'] else ''
            writer.writerow([h['id'], h['user_id'], h['temperature'], h['bp_sys'], h['bp_dia'], h['heart_rate'], h['blood_sugar'], h['oxygen_level'], created_at_str])

    # Export doctors.csv
    doctors_path = os.path.join(BASE_DIR, 'doctors.csv')
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, name, specialty, specialty_name, clinic, rating, experience, image FROM doctors')
        docs = cur.fetchall()
    finally:
        cur.close()
        conn.close()
        
    with open(doctors_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'specialty', 'specialty_name', 'clinic', 'rating', 'experience', 'image'])
        for d in docs:
            writer.writerow([d['id'], d['name'], d['specialty'], d['specialty_name'], d['clinic'], d['rating'], d['experience'], d['image']])



init_db()

def find_user_by_identifier(identifier):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email, password FROM users WHERE email = %s OR username = %s', (identifier, identifier))
    row = cur.fetchone()
    cur.close()
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
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cur.fetchone():
            return jsonify({'error': 'Email already registered'}), 409

        pwd_hash = generate_password_hash(password)
        cur.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id', (username, email, pwd_hash))
        user_id = cur.fetchone()['id']
        conn.commit()
        
        session['user_id'] = user_id
        # update excel export
        try:
            export_to_excel()
            export_csvs()
        except Exception:
            pass
        return jsonify({'id': user_id, 'username': username, 'email': email}), 201
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': 'Server error'}), 500
    finally:
        cur.close()
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
    cur = conn.cursor()
    cur.execute('SELECT id, username, email, age, gender, blood_group, phone, address, medical_history FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(row))

@app.route('/api/user/profile', methods=['PUT'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json() or {}
    age = data.get('age')
    gender = data.get('gender')
    blood_group = data.get('blood_group')
    phone = data.get('phone')
    address = data.get('address')
    medical_history = data.get('medical_history')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            UPDATE users 
            SET age = %s, gender = %s, blood_group = %s, phone = %s, address = %s, medical_history = %s
            WHERE id = %s
        ''', (age, gender, blood_group, phone, address, medical_history, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'ok': True}), 200
    except Exception as e:
        print(f"Profile update error: {e}")
        return jsonify({'error': 'Server error'}), 500

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
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO appointments (user_id, patient_name, email, phone, doctor, date, time, reason) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
            (user_id, patient_name, email, phone, doctor, date, time, reason)
        )
        appt_id = cur.fetchone()['id']
        conn.commit()
        
        cur.execute('SELECT id, patient_name, email, phone, doctor, date, time, reason, created_at FROM appointments WHERE id = %s', (appt_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            # PostgreSQL datetime object conversion
            row_dict = dict(row)
            row_dict['created_at'] = str(row_dict['created_at'])
            
            # update excel export
            try:
                export_to_excel()
                export_csvs()
            except Exception:
                pass
            return jsonify(row_dict), 201
        return jsonify({'error': 'Failed to create appointment'}), 500
    except Exception as e:
        print(f"Appointment error: {e}")
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/appointments', methods=['GET'])
def list_appointments():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, patient_name, email, phone, doctor, date, time, reason, status, cancel_reason, created_at FROM appointments WHERE user_id = %s ORDER BY created_at DESC', (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        res = []
        for r in rows:
            d = dict(r)
            d['created_at'] = str(d['created_at'])
            res.append(d)
        return jsonify(res)
    except Exception as e:
        print(f"List appointments error: {e}")
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/appointments/<int:appt_id>', methods=['DELETE'])
def delete_appointment(appt_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM appointments WHERE id = %s', (appt_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({'error': 'Appointment not found'}), 404
        if row['user_id'] != user_id:
            cur.close()
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403

        cur.execute('DELETE FROM appointments WHERE id = %s', (appt_id,))
        conn.commit()
        cur.close()
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
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO health_data (user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (user_id, data.get('temperature'), data.get('bp_sys'), data.get('bp_dia'), data.get('heart_rate'), data.get('blood_sugar'), data.get('oxygen_level'))
        )
        conn.commit()
        cur.close()
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
        cur = conn.cursor()
        cur.execute('SELECT id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at as timestamp FROM health_data WHERE user_id = %s ORDER BY created_at ASC', (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        res = []
        for r in rows:
            d = dict(r)
            d['timestamp'] = str(d['timestamp'])
            res.append(d)
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/doctors', methods=['GET'])
def list_doctors():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, name, specialty, specialty_name, clinic, rating, experience, image FROM doctors')
        rows = cur.fetchall()
        cur.close()
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
        cur = conn.cursor()
        cur.execute('SELECT name, specialty_name FROM doctors')
        docs = cur.fetchall()
        cur.close()
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

@app.route('/api/doctor/signup', methods=['POST'])
def doctor_signup():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password')
    specialty = (data.get('specialty') or '').strip()
    clinic = (data.get('clinic') or '').strip()
    experience = (data.get('experience') or '').strip()
    
    if not name or not email or not password or not specialty or not clinic or not experience:
        return jsonify({'error': 'All fields are required'}), 400
        
    specialty_map = {
        'general': 'General Physician',
        'cardiology': 'Cardiology',
        'pediatrics': 'Pediatrics',
        'dermatology': 'Dermatology'
    }
    specialty_name = specialty_map.get(specialty.lower(), 'General Physician')
    hashed_password = generate_password_hash(password)
    
    try:
        conn = get_db()
        cur = conn.cursor()
        # Check if email or name exists
        cur.execute('SELECT id FROM doctors WHERE email = %s OR name = %s', (email, name))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Doctor with this email or name already exists'}), 409
            
        cur.execute(
            '''INSERT INTO doctors (name, email, password, specialty, specialty_name, clinic, experience, rating, image)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
            (name, email, hashed_password, specialty, specialty_name, clinic, experience, 5.0, 'male_doctor.png')
        )
        doc_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        # Log them in automatically
        session['doctor_id'] = doc_id
        session['doctor_name'] = name
        
        return jsonify({
            'id': doc_id,
            'name': name,
            'email': email
        }), 201
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/doctor/login', methods=['POST'])
def doctor_login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
        
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, name, email, password FROM doctors WHERE email = %s', (email,))
        doc = cur.fetchone()
        cur.close()
        conn.close()
        
        if doc and check_password_hash(doc['password'], password):
            session['doctor_id'] = doc['id']
            session['doctor_name'] = doc['name']
            return jsonify({
                'id': doc['id'],
                'name': doc['name'],
                'email': doc['email']
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/doctor/me', methods=['GET'])
def doctor_me():
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, name, email, specialty_name, clinic FROM doctors WHERE id = %s', (doctor_id,))
        doc = cur.fetchone()
        cur.close()
        conn.close()
        if doc:
            return jsonify(dict(doc))
        return jsonify({'error': 'Doctor not found'}), 404
    except Exception:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/doctor/logout', methods=['POST'])
def doctor_logout():
    session.pop('doctor_id', None)
    session.pop('doctor_name', None)
    return jsonify({'ok': True}), 200

@app.route('/api/doctor/appointments', methods=['GET'])
def doctor_appointments():
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db()
        cur = conn.cursor()
        # Find the doctor's name to match in the appointments table
        cur.execute('SELECT name FROM doctors WHERE id = %s', (doctor_id,))
        doc = cur.fetchone()
        if not doc:
            cur.close()
            conn.close()
            return jsonify({'error': 'Doctor not found'}), 404
            
        doctor_name = doc['name']
        cur.execute('SELECT id, user_id, patient_name, email, phone, date, time, reason, status, cancel_reason, created_at FROM appointments WHERE doctor = %s ORDER BY created_at DESC', (doctor_name,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        res = []
        for r in rows:
            d = dict(r)
            d['created_at'] = str(d['created_at'])
            res.append(d)
        return jsonify(res)
    except Exception as e:
        print(f"Doctor appointments error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/doctor/appointments/<int:appt_id>/status', methods=['PUT'])
def update_appointment_status(appt_id):
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json() or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
        
    try:
        conn = get_db()
        cur = conn.cursor()
        # Verify the appointment belongs to this doctor
        cur.execute('SELECT doctor FROM appointments WHERE id = %s', (appt_id,))
        appt = cur.fetchone()
        if not appt:
            cur.close()
            conn.close()
            return jsonify({'error': 'Appointment not found'}), 404
            
        cur.execute('SELECT name FROM doctors WHERE id = %s', (doctor_id,))
        doc = cur.fetchone()
        if not doc or doc['name'] != appt['doctor']:
            cur.close()
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
            
        cancel_reason = data.get('cancel_reason')
        if new_status == 'Cancelled' and cancel_reason:
            cur.execute('UPDATE appointments SET status = %s, cancel_reason = %s WHERE id = %s', (new_status, cancel_reason, appt_id))
        else:
            cur.execute('UPDATE appointments SET status = %s WHERE id = %s', (new_status, appt_id))
            
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'ok': True, 'status': new_status})
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/doctor/patient/<int:user_id>', methods=['GET'])
def get_patient_report(user_id):
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Verify doctor is allowed to see this user (i.e. user booked an appointment with them)
        cur.execute('SELECT name FROM doctors WHERE id = %s', (doctor_id,))
        doc = cur.fetchone()
        if not doc:
            return jsonify({'error': 'Unauthorized'}), 403
            
        cur.execute('SELECT 1 FROM appointments WHERE doctor = %s AND user_id = %s LIMIT 1', (doc['name'], user_id))
        if not cur.fetchone():
            return jsonify({'error': 'Unauthorized to view this patient'}), 403
            
        # Fetch user profile
        cur.execute('SELECT username, email, age, gender, blood_group, phone, address, medical_history FROM users WHERE id = %s', (user_id,))
        profile = cur.fetchone()
        if not profile:
            return jsonify({'error': 'Patient not found'}), 404
            
        # Fetch health data history
        cur.execute('SELECT temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at FROM health_data WHERE user_id = %s ORDER BY created_at ASC', (user_id,))
        health_rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        health_data = []
        for r in health_rows:
            d = dict(r)
            d['created_at'] = str(d['created_at'])
            health_data.append(d)
            
        return jsonify({
            'profile': dict(profile),
            'health_data': health_data
        }), 200
    except Exception as e:
        print(f"Report error: {e}")
        return jsonify({'error': 'Server error'}), 500

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
