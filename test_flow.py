import requests, sys, time, os
BASE = 'http://localhost:3000'
email = f'testuser+{int(time.time())}@example.com'
password = 'TestPass123'
username = 'testuser'

s = requests.Session()
try:
    print('Signing up:', email)
    r = s.post(f'{BASE}/api/signup', json={'username': username, 'email': email, 'password': password}, timeout=10)
    print('signup', r.status_code, r.text)
    if r.status_code == 409:
        # already exists, try login
        print('Email exists, logging in')
        r = s.post(f'{BASE}/api/login', json={'identifier': email, 'password': password}, timeout=10)
        print('login', r.status_code, r.text)
        if not r.ok:
            raise SystemExit('Login failed')

    # create appointment
    appt = {
        'patient_name': 'Test User',
        'email': email,
        'phone': '555-000-1111',
        'doctor': 'Dr. Test',
        'date': time.strftime('%Y-%m-%d'),
        'time': '10:00 AM',
        'reason': 'Testing CSV export'
    }
    r = s.post(f'{BASE}/api/appointments', json=appt, timeout=10)
    print('create appointment', r.status_code, r.text)

    # wait a moment for exports
    time.sleep(1)

    # print CSV files
    for fn in ('users.csv', 'appointments.csv'):
        path = os.path.join(os.getcwd(), fn)
        print('\n---', fn, 'exists=', os.path.exists(path))
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().splitlines()
                for i,l in enumerate(lines[:20]):
                    print(f'{i+1}: {l}')
        else:
            print(fn, 'not found')

except Exception as e:
    print('error', e)
    sys.exit(1)
