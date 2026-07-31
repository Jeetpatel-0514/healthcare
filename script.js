// ========== Global Variables ==========
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let selectedDate = null;

// ========== Doctor Data ==========
// ========== Doctor Data ==========
let doctors = [];

// ========== Chatbot Knowledge Base ==========
// Removed static responses in favor of ChatGPT backend API integration.

// ========== Initialization ==========
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeDoctors();
    initializeCalendar();
    initializeChatbot();
    initializeHealthMonitor();
    initializeThemeToggle();
    initializeContactForm();
    initializeAuth();
});

// ========== Authentication / Session ==========
let currentUser = null;

function initializeAuth() {
    checkAuth();

    // Wire a logout handler (will be attached to dynamic logout link)
    document.addEventListener('click', (e) => {
        if (e.target && e.target.id === 'logoutLink') {
            e.preventDefault();
            handleLogout();
        }
    });
}

async function checkAuth() {
    try {
        const res = await fetch('/api/me', { credentials: 'include' });
        if (res.ok) {
            currentUser = await res.json();
        } else {
            currentUser = null;
        }
    } catch (err) {
        currentUser = null;
    }
    updateAuthUI();
    autofillPatientInfo();
}

function updateAuthUI() {
    const navMenu = document.getElementById('navMenu');
    if (!navMenu) return;

    // Remove existing auth links if any
    navMenu.querySelectorAll('.auth-link').forEach(el => el.remove());

    if (currentUser) {
        // Add profile and logout links
        const profileLi = document.createElement('li');
        profileLi.className = 'auth-link';
        profileLi.innerHTML = `<a href="user_profile.html" class="nav-link" title="View Profile"><i class="fas fa-user-circle"></i> ${currentUser.username}</a>`;
        const logoutLi = document.createElement('li');
        logoutLi.className = 'auth-link';
        logoutLi.innerHTML = `<a href="#" id="logoutLink" class="nav-link"><i class="fas fa-sign-out-alt"></i> LOGOUT</a>`;
        navMenu.appendChild(profileLi);
        navMenu.appendChild(logoutLi);
    } else {
        // Add unified login / signup link
        const loginLi = document.createElement('li');
        loginLi.className = 'auth-link';
        loginLi.innerHTML = `<a href="login.html" class="nav-link"><i class="fas fa-sign-in-alt"></i> LOGIN / SIGN UP</a>`;
        navMenu.appendChild(loginLi);
    }
}

async function handleLogout() {
    try {
        await fetch('/api/logout', { method: 'POST', credentials: 'include' });
    } catch (e) {
        // ignore
    }
    currentUser = null;
    updateAuthUI();
    window.location.href = 'index.html';
}

function autofillPatientInfo() {
    if (!currentUser) return;
    const nameEl = document.getElementById('patientName');
    const emailEl = document.getElementById('patientEmail');
    if (emailEl && !emailEl.value) emailEl.value = currentUser.email || '';
    if (nameEl && !nameEl.value) nameEl.value = currentUser.username || '';
}

// ========== Navigation Functions ==========
function initializeNavigation() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Hamburger menu toggle
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });
    
    // Close menu when clicking on a link
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
            
            // Update active link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
    
    // Update active link on scroll
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('section');
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').substring(1) === current) {
                link.classList.add('active');
            }
        });
    });
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// ========== Doctor Functions ==========
async function initializeDoctors() {
    // Hardcoded fallback data in case the backend API is not running
    const fallbackDoctors = [
        { name: "Dr. Dhaval Pandya", specialty: "general", specialtyName: "General Physician", clinic: "Impulse Hospital & ICU", rating: 4.9, experience: "18 years", image: "dr.dhaval.webp" },
        { name: "Dr. Gopal Shah", specialty: "cardiology", specialtyName: "Cardiology", clinic: "Heart Care Hospital", rating: 4.9, experience: "20 years", image: "male_doctor.png" },
        { name: "Dr. Apoorva Shah", specialty: "pediatrics", specialtyName: "Pediatrics", clinic: "Children's Health Clinic", rating: 4.7, experience: "12 years", image: "male_doctor.png" },
        { name: "Dr. Dipak Patel", specialty: "dermatology", specialtyName: "Dermatology", clinic: "Skin Care Institute", rating: 4.6, experience: "10 years", image: "male_doctor.png" },
        { name: "Dr. Rajnikant Dave", specialty: "general", specialtyName: "General Physician", clinic: "Community Health Center", rating: 4.8, experience: "18 years", image: "male_doctor.png" },
        { name: "Dr. Payal Joshi", specialty: "cardiology", specialtyName: "Cardiology", clinic: "Advanced Cardiac Care", rating: 4.9, experience: "25 years", image: "female_doctor.png" },
        { name: "Dr. Kavita Patel", specialty: "pediatrics", specialtyName: "Pediatrics", clinic: "Kids First Medical", rating: 4.8, experience: "14 years", image: "female_doctor.png" },
        { name: "Dr. Rajesh Patel", specialty: "dermatology", specialtyName: "Dermatology", clinic: "Derma Wellness Center", rating: 4.7, experience: "16 years", image: "male_doctor.png" }
    ];

    try {
        const res = await fetch('/api/doctors');
        if (res.ok) {
            const data = await res.json();
            // Map the backend's snake_case to the frontend's camelCase
            doctors = data.map(doc => ({
                ...doc,
                specialtyName: doc.specialty_name || doc.specialtyName
            }));
        } else {
            console.warn("Backend /api/doctors returned an error, using fallback data.");
            doctors = fallbackDoctors;
        }
    } catch (err) {
        console.warn('Failed to fetch doctors (server might not be running). Using fallback data.', err);
        doctors = fallbackDoctors;
    }
    
    renderDoctors('all');
    populateDoctorSelect();
    
    // Filter buttons
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const specialty = btn.getAttribute('data-specialty');
            renderDoctors(specialty);
        });
    });
}

function renderDoctors(specialty) {
    const doctorsGrid = document.getElementById('doctorsGrid');
    const filteredDoctors = specialty === 'all' 
        ? doctors 
        : doctors.filter(doc => doc.specialty === specialty);
    
    doctorsGrid.innerHTML = filteredDoctors.map(doctor => `
        <div class="doctor-card">
            <div class="doctor-image">
                <img src="${doctor.image || ''}" alt="${doctor.name}" style="width: 100%; height: 100%; object-fit: cover;">
                <div class="doctor-rating">
                    <i class="fas fa-star"></i>
                    <span>${doctor.rating}</span>
                </div>
            </div>
            <div class="doctor-info">
                <h3 class="doctor-name">${doctor.name}</h3>
                <p class="doctor-specialty">${doctor.specialtyName}</p>
                <p class="doctor-clinic">
                    <i class="fas fa-hospital"></i>
                    ${doctor.clinic}
                </p>
                <button class="btn btn-primary" onclick="bookDoctorAppointment('${doctor.name}')">
                    <i class="fas fa-calendar-check"></i> Book Appointment
                </button>
            </div>
        </div>
    `).join('');
}

function bookDoctorAppointment(doctorName) {
    scrollToSection('appointments');
    
    // Pre-select the doctor in the appointment form
    setTimeout(() => {
        const doctorSelect = document.getElementById('doctorSelect');
        doctorSelect.value = doctorName;
    }, 500);
}

function populateDoctorSelect() {
    const doctorSelect = document.getElementById('doctorSelect');
    doctors.forEach(doctor => {
        const option = document.createElement('option');
        option.value = doctor.name;
        option.textContent = `${doctor.name} - ${doctor.specialtyName}`;
        doctorSelect.appendChild(option);
    });
}

// ========== Calendar Functions ==========
function initializeCalendar() {
    renderCalendar();
    
    document.getElementById('prevMonth').addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    });
    
    document.getElementById('nextMonth').addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    });
    
    // Appointment form submission
    document.getElementById('appointmentForm').addEventListener('submit', handleAppointmentSubmit);
}

function renderCalendar() {
    const monthNames = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"];
    
    document.getElementById('currentMonth').textContent = `${monthNames[currentMonth]} ${currentYear}`;
    
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today = new Date();
    
    const calendarDates = document.getElementById('calendarDates');
    calendarDates.innerHTML = '';
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('div');
        calendarDates.appendChild(emptyCell);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const dateCell = document.createElement('div');
        dateCell.className = 'calendar-date';
        dateCell.textContent = day;
        
        const cellDate = new Date(currentYear, currentMonth, day);
        
        // Disable past dates
        if (cellDate < today.setHours(0, 0, 0, 0)) {
            dateCell.classList.add('disabled');
        } else {
            dateCell.addEventListener('click', () => selectDate(day));
        }
        
        calendarDates.appendChild(dateCell);
    }
}

function selectDate(day) {
    selectedDate = new Date(currentYear, currentMonth, day);
    
    // Update visual selection
    document.querySelectorAll('.calendar-date').forEach(cell => {
        cell.classList.remove('selected');
    });
    event.target.classList.add('selected');
}

function handleAppointmentSubmit(e) {
    e.preventDefault();
    
    if (!selectedDate) {
        alert('Please select a date from the calendar');
        return;
    }
    const name = document.getElementById('patientName').value;
    const email = document.getElementById('patientEmail').value;
    const phone = document.getElementById('patientPhone').value;
    const doctor = document.getElementById('doctorSelect').value;
    const time = document.getElementById('timeSlot').value;
    const reason = document.getElementById('appointmentReason').value;

    // Show loading
    showLoading();

    // Prepare payload
    const payload = {
        patient_name: name,
        email,
        phone,
        doctor,
        date: selectedDate.toISOString().split('T')[0],
        time,
        reason
    };

    fetch('/api/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
    }).then(async res => {
        hideLoading();
        if (res.ok) {
            const appt = await res.json();
            showAppointmentConfirmation({
                name: appt.patient_name || name,
                email: appt.email || email,
                phone: appt.phone || phone,
                doctor: appt.doctor || doctor,
                date: new Date(appt.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }),
                time: appt.time || time,
                reason: appt.reason || reason
            });
            // Reset form
            document.getElementById('appointmentForm').reset();
            selectedDate = null;
            document.querySelectorAll('.calendar-date').forEach(cell => {
                cell.classList.remove('selected');
            });
            // Redirect to My Appointments after short delay
            setTimeout(() => { window.location.href = 'my_appointments.html'; }, 900);
        } else if (res.status === 401) {
            alert('Please log in to book an appointment.');
            window.location.href = 'login.html';
        } else {
            const err = await res.json().catch(() => ({}));
            alert(err.error || 'Failed to create appointment');
        }
    }).catch(err => {
        hideLoading();
        alert('Network error');
    });
}

function showAppointmentConfirmation(details) {
    const modal = document.getElementById('appointmentModal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <p><strong>Patient:</strong> ${details.name}</p>
        <p><strong>Email:</strong> ${details.email}</p>
        <p><strong>Phone:</strong> ${details.phone}</p>
        <p><strong>Doctor:</strong> ${details.doctor}</p>
        <p><strong>Date:</strong> ${details.date}</p>
        <p><strong>Time:</strong> ${details.time}</p>
        <p><strong>Reason:</strong> ${details.reason}</p>
        <p style="margin-top: 20px; color: var(--success);">
            <i class="fas fa-check-circle"></i> 
            A confirmation email has been sent to ${details.email}
        </p>
    `;
    
    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('appointmentModal').classList.remove('active');
}

// ========== Chatbot Functions ==========
function initializeChatbot() {
    const chatbotInput = document.getElementById('chatbotInput');
    
    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

function toggleChatbot() {
    const chatbot = document.getElementById('chatbotWidget');
    const toggle = document.getElementById('chatbotToggle');
    const badge = toggle.querySelector('.notification-badge');
    
    chatbot.classList.toggle('active');
    
    if (chatbot.classList.contains('active')) {
        toggle.style.display = 'none';
        if (badge) badge.style.display = 'none';
    } else {
        toggle.style.display = 'flex';
    }
}

function openChatbot() {
    const chatbot = document.getElementById('chatbotWidget');
    const toggle = document.getElementById('chatbotToggle');
    const badge = toggle.querySelector('.notification-badge');
    
    chatbot.classList.add('active');
    toggle.style.display = 'none';
    if (badge) badge.style.display = 'none';
}

function closeChatbot() {
    const chatbot = document.getElementById('chatbotWidget');
    const toggle = document.getElementById('chatbotToggle');
    
    chatbot.classList.remove('active');
    toggle.style.display = 'flex';
}

async function sendMessage() {
    const input = document.getElementById('chatbotInput');
    const message = input.value.trim();
    
    if (message === '') return;
    
    // Add user message
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    addTypingIndicator(typingId);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ message })
        });
        
        removeTypingIndicator(typingId);
        
        if (response.ok) {
            const data = await response.json();
            addChatMessage(data.text, 'bot');
            if (data.action) {
                addChatActionButtons(data.action);
            }
        } else {
            addChatMessage(`Sorry, I am having trouble connecting to the server. (Status code: ${response.status})`, 'bot');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addChatMessage('Sorry, there was a network error. Ensure the Python server is running.', 'bot');
    }
}

async function sendQuickReply(message) {
    // Remove quick reply buttons
    document.querySelectorAll('.quick-replies').forEach(el => el.remove());
    
    // Add user message
    addChatMessage(message, 'user');
    
    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    addTypingIndicator(typingId);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ message })
        });
        
        removeTypingIndicator(typingId);
        
        if (response.ok) {
            const data = await response.json();
            addChatMessage(data.text, 'bot');
            if (data.action) {
                addChatActionButtons(data.action);
            }
        } else {
            addChatMessage(`Sorry, I am having trouble connecting to the server. (Status code: ${response.status})`, 'bot');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addChatMessage('Sorry, there was a network error. Ensure the Python server is running.', 'bot');
    }
}

function addTypingIndicator(id) {
    const messagesContainer = document.getElementById('chatbotMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message typing-indicator-msg';
    messageDiv.id = id;
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <p>...</p>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function addChatMessage(text, sender) {
    const messagesContainer = document.getElementById('chatbotMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-${sender === 'bot' ? 'robot' : 'user'}"></i>
        </div>
        <div class="message-content">
            <p>${text.replace(/\n/g, '<br>')}</p>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addChatActionButtons(action) {
    const messagesContainer = document.getElementById('chatbotMessages');
    const lastMessage = messagesContainer.lastElementChild;
    const messageContent = lastMessage.querySelector('.message-content');
    
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'quick-replies';
    
    if (action === 'doctors') {
        actionsDiv.innerHTML = `
            <button class="quick-reply" onclick="scrollToSection('doctors'); closeChatbot();">
                View Doctors
            </button>
        `;
    } else if (action === 'appointments') {
        actionsDiv.innerHTML = `
            <button class="quick-reply" onclick="scrollToSection('appointments'); closeChatbot();">
                Book Appointment
            </button>
        `;
    }
    
    messageContent.appendChild(actionsDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ========== Health Monitor Functions ==========
let healthCharts = {};

function initializeHealthMonitor() {
    document.getElementById('healthForm').addEventListener('submit', handleHealthSubmit);
    renderHealthCharts();
}

function handleHealthSubmit(e) {
    e.preventDefault();
    
    const temperature = parseFloat(document.getElementById('temperature').value);
    const bpSys = parseInt(document.getElementById('bloodPressureSys').value);
    const bpDia = parseInt(document.getElementById('bloodPressureDia').value);
    const heartRate = parseInt(document.getElementById('heartRate').value);
    const bloodSugar = parseInt(document.getElementById('bloodSugar').value);
    const oxygenLevel = parseFloat(document.getElementById('oxygenLevel').value);
    
    const results = analyzeHealthData({
        temperature,
        bpSys,
        bpDia,
        heartRate,
        bloodSugar,
        oxygenLevel
    });
    
    displayHealthResults(results);
    saveHealthData({ 
        temperature, 
        bp_sys: bpSys, 
        bp_dia: bpDia, 
        heart_rate: heartRate, 
        blood_sugar: bloodSugar, 
        oxygen_level: oxygenLevel 
    });
}

function analyzeHealthData(data) {
    const results = [];
    
    // Temperature analysis
    if (data.temperature) {
        let status, message;
        if (data.temperature < 97.0) {
            status = 'warning';
            message = 'Your body temperature is below normal. You may be experiencing hypothermia. Please keep warm and consult a doctor if symptoms persist.';
        } else if (data.temperature >= 97.0 && data.temperature <= 99.0) {
            status = 'normal';
            message = 'Your body temperature is within the normal range. This is a healthy reading.';
        } else if (data.temperature > 99.0 && data.temperature <= 100.4) {
            status = 'warning';
            message = 'You have a slight elevation in temperature. Monitor your symptoms and rest. If it increases, consult a doctor.';
        } else {
            status = 'danger';
            message = 'You have a fever. Rest, stay hydrated, and take fever reducers. If fever persists above 103°F or lasts more than 3 days, seek medical attention.';
        }
        results.push({ name: 'Body Temperature', value: `${data.temperature}°F`, status, message });
    }
    
    // Blood Pressure analysis
    if (data.bpSys && data.bpDia) {
        let status, message;
        if (data.bpSys < 90 || data.bpDia < 60) {
            status = 'warning';
            message = 'Your blood pressure is low. This may cause dizziness or fainting. Stay hydrated and consult a doctor if symptoms persist.';
        } else if (data.bpSys >= 90 && data.bpSys <= 120 && data.bpDia >= 60 && data.bpDia <= 80) {
            status = 'normal';
            message = 'Your blood pressure is within the normal range. Keep maintaining a healthy lifestyle.';
        } else if (data.bpSys <= 139 || data.bpDia <= 89) {
            status = 'warning';
            message = 'Your blood pressure is elevated. Consider lifestyle changes like reducing salt intake, exercising, and managing stress.';
        } else {
            status = 'danger';
            message = 'Your blood pressure is high. Please consult a cardiologist for proper evaluation and treatment.';
        }
        results.push({ name: 'Blood Pressure', value: `${data.bpSys}/${data.bpDia} mmHg`, status, message });
    }
    
    // Heart Rate analysis
    if (data.heartRate) {
        let status, message;
        if (data.heartRate < 60) {
            status = 'warning';
            message = 'Your heart rate is below normal (bradycardia). If you\'re an athlete, this may be normal. Otherwise, consult a cardiologist.';
        } else if (data.heartRate >= 60 && data.heartRate <= 100) {
            status = 'normal';
            message = 'Your heart rate is within the normal resting range. This indicates good cardiovascular health.';
        } else {
            status = 'danger';
            message = 'Your heart rate is elevated (tachycardia). If you\'re at rest, this requires medical attention. Consult a cardiologist.';
        }
        results.push({ name: 'Heart Rate', value: `${data.heartRate} bpm`, status, message });
    }
    
    // Blood Sugar analysis
    if (data.bloodSugar) {
        let status, message;
        if (data.bloodSugar < 70) {
            status = 'danger';
            message = 'Your blood sugar is low (hypoglycemia). Consume fast-acting carbohydrates immediately and monitor closely.';
        } else if (data.bloodSugar >= 70 && data.bloodSugar <= 100) {
            status = 'normal';
            message = 'Your fasting blood sugar level is normal. Continue maintaining a balanced diet and regular exercise.';
        } else if (data.bloodSugar <= 125) {
            status = 'warning';
            message = 'Your blood sugar is elevated (prediabetes range). Consider dietary changes and consult a doctor for guidance.';
        } else {
            status = 'danger';
            message = 'Your blood sugar is high (diabetes range). Please consult a doctor for proper evaluation and treatment plan.';
        }
        results.push({ name: 'Blood Sugar', value: `${data.bloodSugar} mg/dL`, status, message });
    }
    
    // Oxygen Saturation analysis
    if (data.oxygenLevel) {
        let status, message;
        if (data.oxygenLevel < 90) {
            status = 'danger';
            message = 'Your oxygen saturation is critically low. Seek immediate medical attention or call emergency services.';
        } else if (data.oxygenLevel >= 90 && data.oxygenLevel < 95) {
            status = 'warning';
            message = 'Your oxygen saturation is below optimal. Monitor closely and consult a doctor if you experience breathing difficulties.';
        } else {
            status = 'normal';
            message = 'Your oxygen saturation is within the normal range. Your blood is carrying adequate oxygen to your organs.';
        }
        results.push({ name: 'Oxygen Saturation', value: `${data.oxygenLevel}%`, status, message });
    }
    
    return results;
}

function displayHealthResults(results) {
    const resultsContainer = document.getElementById('healthResults');
    
    if (results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clipboard-list"></i>
                <p>Please enter at least one health parameter to see results</p>
            </div>
        `;
        return;
    }
    
    resultsContainer.innerHTML = results.map(result => `
        <div class="health-result-item ${result.status}">
            <h4>${result.name}: ${result.value}</h4>
            <p>${result.message}</p>
            <span class="health-status-badge ${result.status}">
                ${result.status === 'normal' ? 'Normal' : result.status === 'warning' ? 'Attention Needed' : 'Urgent'}
            </span>
        </div>
    `).join('');
}

async function saveHealthData(data) {
    if (!currentUser) {
        alert('Please log in to save your health data.');
        return;
    }
    try {
        const res = await fetch('/api/health', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        if (res.ok) {
            renderHealthCharts();
        }
    } catch (err) {
        console.error('Failed to save health data:', err);
    }
}

async function renderHealthCharts() {
    let history = [];
    try {
        const res = await fetch('/api/health', { credentials: 'include' });
        if (res.ok) {
            history = await res.json();
        }
    } catch (err) {
        console.error('Failed to fetch health history:', err);
    }

    if (history.length === 0) {
        // Clear charts if no data
        Object.values(healthCharts).forEach(chart => {
            chart.data.labels = [];
            chart.data.datasets.forEach(ds => ds.data = []);
            chart.update();
        });
        return;
    }
    
    const labels = history.map(entry => {
        const d = new Date(entry.timestamp);
        return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`;
    });
    
    const themeColor = getComputedStyle(document.body).getPropertyValue('--primary-color').trim() || '#3498db';
    
    const createOrUpdateChart = (canvasId, label, dataPoints, borderColor = themeColor, extraDataset = null) => {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const datasets = [{
            label: label,
            data: dataPoints,
            borderColor: borderColor,
            backgroundColor: borderColor + '33', // 20% opacity
            borderWidth: 2,
            tension: 0.3,
            fill: true
        }];
        
        if (extraDataset) datasets.push(extraDataset);
        
        if (healthCharts[canvasId]) {
            healthCharts[canvasId].data.labels = labels;
            healthCharts[canvasId].data.datasets = datasets;
            healthCharts[canvasId].update();
        } else {
            healthCharts[canvasId] = new Chart(ctx, {
                type: 'line',
                data: { labels: labels, datasets: datasets },
                options: {
                    responsive: true,
                    plugins: { legend: { display: true } },
                    scales: { x: { display: true }, y: { display: true } }
                }
            });
        }
    };
    
    createOrUpdateChart('tempChart', 'Temperature (°F)', history.map(h => h.temperature).filter(x => x), '#e74c3c');
    
    const bpSysData = history.map(h => h.bp_sys).filter(x => x);
    const bpDiaData = history.map(h => h.bp_dia).filter(x => x);
    if(bpSysData.length > 0 && bpDiaData.length > 0) {
        createOrUpdateChart('bpChart', 'Systolic', bpSysData, '#e74c3c', {
            label: 'Diastolic',
            data: bpDiaData,
            borderColor: '#3498db',
            backgroundColor: '#3498db33',
            borderWidth: 2,
            tension: 0.3,
            fill: true
        });
    }
    
    createOrUpdateChart('hrChart', 'Heart Rate (bpm)', history.map(h => h.heart_rate).filter(x => x), '#e67e22');
    createOrUpdateChart('bsChart', 'Blood Sugar (mg/dL)', history.map(h => h.blood_sugar).filter(x => x), '#9b59b6');
    createOrUpdateChart('o2Chart', 'Oxygen Saturation (%)', history.map(h => h.oxygen_level).filter(x => x), '#2ecc71');
}

// ========== Theme Toggle ==========
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        
        if (body.classList.contains('dark-mode')) {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            localStorage.setItem('theme', 'dark');
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            localStorage.setItem('theme', 'light');
        }
    });
}

// ========== Contact Form ==========
function initializeContactForm() {
    document.getElementById('contactForm').addEventListener('submit', (e) => {
        e.preventDefault();
        
        showLoading();
        
        setTimeout(() => {
            hideLoading();
            alert('Thank you for contacting us! We will get back to you within 24 hours.');
            e.target.reset();
        }, 1500);
    });
}

// ========== Loading Functions ==========
function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// ========== Utility Functions ==========
// Close modal when clicking outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('appointmentModal');
    if (e.target === modal) {
        closeModal();
    }
});

// Smooth scroll for all anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});
