# Multi-Framework Login System

A comprehensive authentication system that demonstrates 4 different backend frameworks working together with a shared database and load balancing.

## Architecture

- **FastAPI** (Python) - Port 8001
- **Django** (Python) - Port 8002
- **Node.js** (Express) - Port 8003
- **.NET 8** (C#) - Port 8004
- **PostgreSQL** - Shared database
- **Nginx** - Load balancer (Round-robin)

## Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd multiframework-login

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up -d

# Access the application
open http://localhost
