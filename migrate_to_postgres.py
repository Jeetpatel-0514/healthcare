import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os

DATABASE_URL = 'postgres://6290082d19f097b7c5e25851ffa205042f661c902ce28788fefbf1320ef402e8:sk_LJ-_367XsS-G5qTJbu3Df@db.prisma.io:5432/postgres?sslmode=require'
SQLITE_DB = 'data.sqlite'

def migrate():
    print("Connecting to SQLite...")
    sl_conn = sqlite3.connect(SQLITE_DB)
    sl_conn.row_factory = sqlite3.Row
    sl_cur = sl_conn.cursor()

    print("Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cur = pg_conn.cursor()

    # Create tables in PostgreSQL
    print("Creating tables in PostgreSQL...")
    pg_cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    pg_cur.execute('''
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    pg_cur.execute('''
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
    pg_cur.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            specialty TEXT,
            specialty_name TEXT,
            clinic TEXT,
            rating REAL,
            experience TEXT,
            image TEXT
        )
    ''')
    pg_conn.commit()

    # Clear existing tables in pg in case it's a rerun
    pg_cur.execute("TRUNCATE TABLE appointments, health_data, doctors, users RESTART IDENTITY CASCADE;")
    pg_conn.commit()

    # Migrate Users
    print("Migrating users...")
    sl_cur.execute("SELECT id, username, email, password FROM users")
    users = sl_cur.fetchall()
    if users:
        execute_batch(pg_cur, 
            "INSERT INTO users (id, username, email, password) VALUES (%s, %s, %s, %s)",
            [(r['id'], r['username'], r['email'], r['password']) for r in users]
        )
        pg_cur.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));")
    
    # Migrate Appointments
    print("Migrating appointments...")
    sl_cur.execute("SELECT id, user_id, patient_name, email, phone, doctor, date, time, reason, created_at FROM appointments")
    appts = sl_cur.fetchall()
    if appts:
        execute_batch(pg_cur,
            "INSERT INTO appointments (id, user_id, patient_name, email, phone, doctor, date, time, reason, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [(r['id'], r['user_id'], r['patient_name'], r['email'], r['phone'], r['doctor'], r['date'], r['time'], r['reason'], r['created_at']) for r in appts]
        )
        pg_cur.execute("SELECT setval('appointments_id_seq', (SELECT MAX(id) FROM appointments));")

    # Migrate Health Data
    print("Migrating health data...")
    sl_cur.execute("SELECT id, user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at FROM health_data")
    hdata = sl_cur.fetchall()
    if hdata:
        execute_batch(pg_cur,
            "INSERT INTO health_data (id, user_id, temperature, bp_sys, bp_dia, heart_rate, blood_sugar, oxygen_level, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [(r['id'], r['user_id'], r['temperature'], r['bp_sys'], r['bp_dia'], r['heart_rate'], r['blood_sugar'], r['oxygen_level'], r['created_at']) for r in hdata]
        )
        pg_cur.execute("SELECT setval('health_data_id_seq', (SELECT MAX(id) FROM health_data));")

    # Migrate Doctors
    print("Migrating doctors...")
    sl_cur.execute("SELECT id, name, specialty, specialty_name, clinic, rating, experience, image FROM doctors")
    docs = sl_cur.fetchall()
    if docs:
        execute_batch(pg_cur,
            "INSERT INTO doctors (id, name, specialty, specialty_name, clinic, rating, experience, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [(r['id'], r['name'], r['specialty'], r['specialty_name'], r['clinic'], r['rating'], r['experience'], r['image']) for r in docs]
        )
        pg_cur.execute("SELECT setval('doctors_id_seq', (SELECT MAX(id) FROM doctors));")

    pg_conn.commit()
    print("Migration complete!")
    sl_conn.close()
    pg_conn.close()

if __name__ == '__main__':
    migrate()
