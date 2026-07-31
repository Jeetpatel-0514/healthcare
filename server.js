require('dotenv').config();
const express = require('express');
const path = require('path');
const bcrypt = require('bcrypt');
const Database = require('better-sqlite3');
const session = require('express-session');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors({ origin: true, credentials: true }));
app.use(session({
  secret: process.env.SESSION_SECRET || 'dev-secret',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 }
}));

// Serve frontend static files (HTML, CSS, JS)
app.use(express.static(path.join(__dirname)));

// Initialize database
const dbFile = process.env.DB_FILE || path.join(__dirname, 'data.sqlite');
const db = new Database(dbFile);

db.prepare(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT UNIQUE,
    password TEXT
  )
`).run();

// Helpers
function findUserByEmailOrUsername(identifier) {
  return db.prepare('SELECT id, username, email, password FROM users WHERE email = ? OR username = ?').get(identifier, identifier);
}

// API routes
app.post('/api/signup', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    if (!username || !email || !password) return res.status(400).json({ error: 'Missing fields' });

    const existing = db.prepare('SELECT id FROM users WHERE email = ?').get(email);
    if (existing) return res.status(409).json({ error: 'Email already registered' });

    const hash = await bcrypt.hash(password, 10);
    const info = db.prepare('INSERT INTO users (username, email, password) VALUES (?, ?, ?)').run(username, email, hash);

    req.session.userId = info.lastInsertRowid;
    res.status(201).json({ id: info.lastInsertRowid, username, email });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/login', async (req, res) => {
  try {
    const { identifier, password } = req.body; // identifier = email or username
    if (!identifier || !password) return res.status(400).json({ error: 'Missing fields' });

    const user = findUserByEmailOrUsername(identifier);
    if (!user) return res.status(401).json({ error: 'Invalid credentials' });

    const ok = await bcrypt.compare(password, user.password);
    if (!ok) return res.status(401).json({ error: 'Invalid credentials' });

    req.session.userId = user.id;
    res.json({ id: user.id, username: user.username, email: user.email });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/me', (req, res) => {
  try {
    const userId = req.session.userId;
    if (!userId) return res.status(401).json({ error: 'Not authenticated' });

    const user = db.prepare('SELECT id, username, email FROM users WHERE id = ?').get(userId);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/logout', (req, res) => {
  req.session.destroy(err => {
    if (err) return res.status(500).json({ error: 'Logout failed' });
    res.json({ ok: true });
  });
});

// Fallback to index.html for any non-API routes (so SPA navigation still works)
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api')) return next();
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
