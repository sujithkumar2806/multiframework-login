FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make wait script executable
RUN chmod +x wait-for-db.sh

# Expose port
EXPOSE 8000

# Use wait-for-db.sh as entrypoint
ENTRYPOINT ["./wait-for-db.sh"]

# Run the application with gunicorn or manage.py
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
