const API_BASE_URL = 'http://multiframework-alb-1441586806.us-east-1.elb.amazonaws.com';
let currentBackend = localStorage.getItem('selectedBackend') || 'fastapi';

function setBackend(backend) {
    currentBackend = backend;
    localStorage.setItem('selectedBackend', backend);
    document.querySelectorAll('.backend-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('backend-name').innerText = backend.toUpperCase();
    showMessage(`Switched to ${backend.toUpperCase()} backend`, 'success');
}

function setMode(mode) {
    if (mode === 'login') {
        document.getElementById('login-form').style.display = 'block';
        document.getElementById('register-form').style.display = 'none';
    } else {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = 'block';
    }
    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function getApiUrl(endpoint) {
    return `${API_BASE_URL}/api/${currentBackend}/${endpoint}`;
}

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    if (!username || !password) {
        showMessage('Please fill all fields', 'error');
        return;
    }
    try {
        const response = await fetch(getApiUrl('login'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('loggedInUser', username);
            localStorage.setItem('userBackend', currentBackend);
            showMessage('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 1000);
        } else {
            showMessage(data.message || data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Network error: ' + error.message, 'error');
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-confirm').value;
    if (!username || !email || !password) {
        showMessage('Please fill all fields', 'error');
        return;
    }
    if (password !== confirm) {
        showMessage('Passwords do not match', 'error');
        return;
    }
    try {
        const response = await fetch(getApiUrl('register'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await response.json();
        if (response.ok) {
            showMessage('Registration successful! Please login.', 'success');
            setMode('login');
            document.getElementById('login-username').value = username;
        } else {
            showMessage(data.message || data.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Register error:', error);
        showMessage('Network error: ' + error.message, 'error');
    }
}

function showMessage(msg, type) {
    const msgDiv = document.getElementById('message');
    msgDiv.textContent = msg;
    msgDiv.className = `message ${type}`;
    msgDiv.style.display = 'block';
    setTimeout(() => { msgDiv.style.display = 'none'; }, 3000);
}

document.getElementById('backend-name').innerText = currentBackend.toUpperCase();
