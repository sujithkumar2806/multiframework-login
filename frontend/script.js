// frontend/script.js
let currentMode = 'login';

async function setMode(mode) {
    currentMode = mode;
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const buttons = document.querySelectorAll('.toggle-btn');
    
    if (mode === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        buttons[0].classList.add('active');
        buttons[1].classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        buttons[0].classList.remove('active');
        buttons[1].classList.add('active');
    }
}

async function showMessage(message, type) {
    const msgDiv = document.getElementById('message');
    msgDiv.textContent = message;
    msgDiv.className = `message ${type}`;
    msgDiv.style.display = 'block';
    setTimeout(() => {
        msgDiv.style.display = 'none';
    }, 3000);
}

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        // Get which backend served the request from response headers
        const backend = response.headers.get('X-Upstream') || 'Unknown';
        
        if (response.ok) {
            showMessage(`Welcome back, ${data.username}! (Served by: ${backend})`, 'success');
            setTimeout(() => {
                showWelcomePage(data.username, backend);
            }, 1000);
        } else {
            showMessage(data.message || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-confirm').value;
    
    if (!username || !email || !password || !confirm) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    
    if (password !== confirm) {
        showMessage('Passwords do not match', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('Password must be at least 6 characters', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        // Get which backend served the request from response headers
        const backend = response.headers.get('X-Upstream') || 'Unknown';
        
        if (response.ok) {
            showMessage(`User ${data.username} created successfully! (Served by: ${backend})`, 'success');
            setTimeout(() => {
                setMode('login');
                document.getElementById('login-username').value = username;
            }, 1500);
        } else {
            showMessage(data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    }
}

function showWelcomePage(username, backend) {
    // Create a beautiful welcome page overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        animation: fadeIn 0.5s ease-in;
    `;
    
    const welcomeCard = document.createElement('div');
    welcomeCard.style.cssText = `
        background: white;
        border-radius: 20px;
        padding: 50px;
        text-align: center;
        max-width: 90%;
        animation: slideUp 0.5s ease-out;
    `;
    
    welcomeCard.innerHTML = `
        <style>
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(50px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        </style>
        <div style="font-size: 64px; margin-bottom: 20px;">🎉</div>
        <h1 style="color: #667eea; margin-bottom: 10px;">Welcome, ${username}!</h1>
        <p style="color: #666; margin-bottom: 30px;">You have successfully logged in to the Multi-Framework System</p>
        <p style="color: #764ba2; margin-bottom: 30px; font-size: 14px;">🤖 Authentication served by: <strong>${backend}</strong></p>
        <button onclick="location.reload()" style="width: auto; padding: 12px 30px;">Logout</button>
    `;
    
    overlay.appendChild(welcomeCard);
    document.body.appendChild(overlay);
}

async function checkFramework() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        const backend = response.headers.get('X-Upstream') || 'Unknown';
        document.getElementById('framework-badge').innerHTML = 
            `Connected to: ${data.framework} (via ${backend}) 🚀`;
    } catch (error) {
        document.getElementById('framework-badge').innerHTML = 
            `Connected to: Unknown`;
    }
}

// Check framework on load and every 5 seconds to show load balancing in action
checkFramework();
setInterval(checkFramework, 5000);