const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const cors = require('cors');
const url = require('url');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Parse DATABASE_URL and add SSL
const dbUrl = process.env.DATABASE_URL || 'postgresql://dbadmin:SecurePass123!@multiframework-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com:5432/postgres';
const parsedUrl = new URL(dbUrl);

const pool = new Pool({
    host: parsedUrl.hostname,
    port: parsedUrl.port || 5432,
    user: parsedUrl.username,
    password: parsedUrl.password,
    database: parsedUrl.pathname.slice(1),
    ssl: { rejectUnauthorized: false }  // Add SSL for AWS RDS
});

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', framework: 'Node.js 🚀' });
});

// Register endpoint
app.post('/api/register', async (req, res) => {
    const { username, email, password } = req.body;
    
    try {
        const hashedPassword = await bcrypt.hash(password, 10);
        await pool.query(
            'INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)',
            [username, email, hashedPassword]
        );
        res.json({ message: 'User created successfully', username: username });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Server error: ' + error.message });
    }
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;
    
    try {
        const result = await pool.query(
            'SELECT id, username, email, password_hash FROM users WHERE username = $1 OR email = $1',
            [username]
        );
        
        if (result.rows.length === 0) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        const user = result.rows[0];
        const validPassword = await bcrypt.compare(password, user.password_hash);
        
        if (!validPassword) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        res.json({ message: 'Login successful', username: user.username });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Server error: ' + error.message });
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Node.js server running on port ${PORT}`);
});
