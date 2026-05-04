const API_BASE_URL = 'http://multiframework-alb-1441586806.us-east-1.elb.amazonaws.com';
let currentBackend = localStorage.getItem('selectedBackend') || 'fastapi';

function setBackend(backend) {
    currentBackend = backend;
    localStorage.setItem('selectedBackend', backend);
    
    // Update button styles with animation
    document.querySelectorAll('.backend-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.transform = 'scale(1)';
    });
    
    const activeBtn = event.target;
    activeBtn.classList.add('active');
    activeBtn.style.transform = 'scale(1.05)';
    activeBtn.style.transition = 'all 0.3s ease';
    
    // Add pulse animation to the badge
    const badge = document.getElementById('backend-badge');
    badge.style.animation = 'pulse 0.5s ease';
    setTimeout(() => {
        badge.style.animation = '';
    }, 500);
    
    // Update displayed backend name with icons
    const backendNames = {
        'fastapi': '🚀 FastAPI',
        'django': '🐍 Django',
        'node': '💚 Node.js',
        'dotnet': '🔷 .NET'
    };
    document.getElementById('backend-name').innerHTML = backendNames[backend];
    
    // Update badge color
    badge.className = `badge-active badge-${backend}`;
    badge.innerHTML = '✓ Active';
    
    showMessage(`✨ Switched to ${backendNames[backend]} backend ✨`, 'success');
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
        showMessage('❌ Please fill all fields', 'error');
        return;
    }
    
    // Show loading state
    const loginBtn = event.target;
    const originalText = loginBtn.innerHTML;
    loginBtn.innerHTML = '⏳ Logging in...';
    loginBtn.disabled = true;
    
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
            showMessage(`✅ Welcome ${username}! Redirecting...`, 'success');
            
            // Flash effect on the badge
            const badge = document.getElementById('backend-badge');
            badge.style.backgroundColor = '#4CAF50';
            badge.style.transform = 'scale(1.1)';
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 1500);
        } else {
            showMessage(data.message || data.detail || '❌ Login failed', 'error');
            loginBtn.innerHTML = originalText;
            loginBtn.disabled = false;
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('❌ Network error: ' + error.message, 'error');
        loginBtn.innerHTML = originalText;
        loginBtn.disabled = false;
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-confirm').value;
    
    if (!username || !email || !password) {
        showMessage('❌ Please fill all fields', 'error');
        return;
    }
    
    if (password !== confirm) {
        showMessage('❌ Passwords do not match', 'error');
        return;
    }
    
    const registerBtn = event.target;
    const originalText = registerBtn.innerHTML;
    registerBtn.innerHTML = '⏳ Creating account...';
    registerBtn.disabled = true;
    
    try {
        const response = await fetch(getApiUrl('register'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('✅ Registration successful! Please login.', 'success');
            setMode('login');
            document.getElementById('login-username').value = username;
            document.getElementById('reg-username').value = '';
            document.getElementById('reg-email').value = '';
            document.getElementById('reg-password').value = '';
            document.getElementById('reg-confirm').value = '';
        } else {
            showMessage(data.message || data.detail || '❌ Registration failed', 'error');
        }
        registerBtn.innerHTML = originalText;
        registerBtn.disabled = false;
    } catch (error) {
        console.error('Register error:', error);
        showMessage('❌ Network error: ' + error.message, 'error');
        registerBtn.innerHTML = originalText;
        registerBtn.disabled = false;
    }
}

function showMessage(msg, type) {
    const msgDiv = document.getElementById('message');
    msgDiv.textContent = msg;
    msgDiv.className = `message ${type}`;
    msgDiv.style.display = 'block';
    msgDiv.style.animation = 'fadeIn 0.3s ease';
    setTimeout(() => {
        msgDiv.style.display = 'none';
    }, 3000);
}

// Add CSS animation for pulse effect
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); background-color: #4CAF50; }
        100% { transform: scale(1); }
    }
    .backend-btn {
        transition: all 0.3s ease !important;
    }
    .backend-btn.active {
        box-shadow: 0 0 20px currentColor !important;
    }
    .badge-active {
        transition: all 0.3s ease;
    }
`;
document.head.appendChild(style);

// Initialize
const backendNames = {
    'fastapi': '🚀 FastAPI',
    'django': '🐍 Django',
    'node': '💚 Node.js',
    'dotnet': '🔷 .NET'
};
document.getElementById('backend-name').innerHTML = backendNames[currentBackend];
const badge = document.getElementById('backend-badge');
badge.className = `badge-active badge-${currentBackend}`;
badge.innerHTML = '✓ Active';

// Set active button style
document.querySelectorAll('.backend-btn').forEach(btn => {
    if (btn.innerText.toLowerCase().includes(currentBackend)) {
        btn.classList.add('active');
        btn.style.transform = 'scale(1.02)';
    }
});
