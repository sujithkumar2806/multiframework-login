#!/bin/bash
set -e

echo "Fetching secrets from AWS Secrets Manager..."

SECRET=$(aws secretsmanager get-secret-value \
  --secret-id multiframework/db-credentials \
  --region us-east-1 \
  --query SecretString \
  --output text)

DB_HOST=$(echo     $SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['DB_HOST'])")
DB_NAME=$(echo     $SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['DB_NAME'])")
DB_USER=$(echo     $SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['DB_USER'])")
DB_PASSWORD=$(echo $SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['DB_PASSWORD'])")
DB_PORT=$(echo     $SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['DB_PORT'])")

cat > /home/ubuntu/multiframework-login/.env << EOF
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_PORT=${DB_PORT}
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DOTNET_DATABASE_URL=Host=${DB_HOST};Database=${DB_NAME};Username=${DB_USER};Password=${DB_PASSWORD}
EOF

chmod 600 /home/ubuntu/multiframework-login/.env
echo "Done. Secrets written to .env"
