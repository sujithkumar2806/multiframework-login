pipeline {
    agent any

    environment {
        AWS_REGION   = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        EC2_HOST     = '10.0.11.125'
        DEPLOY_PATH  = '/home/ubuntu/multiframework-login'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Detect changes') {
            steps {
                script {
                    env.GIT_SHA = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()

                    def changed = sh(
                        script: "git diff --name-only HEAD~1 HEAD 2>/dev/null || echo 'all'",
                        returnStdout: true
                    ).trim()

                    echo "Git SHA: ${env.GIT_SHA}"
                    echo "Changed:\n${changed}"

                    env.BUILD_FASTAPI      = (changed.contains('fastapi-server/')  || changed == 'all') ? 'true' : 'false'
                    env.BUILD_DJANGO       = (changed.contains('django-server/')   || changed == 'all') ? 'true' : 'false'
                    env.BUILD_NODE         = (changed.contains('node-server/')     || changed == 'all') ? 'true' : 'false'
                    env.BUILD_DOTNET       = (changed.contains('dotnet-server/')   || changed == 'all') ? 'true' : 'false'
                    env.CONFIG_CHANGED     = (changed.contains('nginx-api.conf')   ||
                                              changed.contains('docker-compose')   ||
                                              changed.contains('prometheus.yml')   ||
                                              changed.contains('alertmanager/')) ? 'true' : 'false'
                }
            }
        }

        stage('Sync code on EC2') {
            steps {
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}
                        git fetch origin
                        git reset --hard origin/main
                        # exclude .env — preserve secrets between runs
                        git clean -fd --exclude=.env

                        aws ecr get-login-password --region ${AWS_REGION} \
                          | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    '
                """
            }
        }

        stage('Load Secrets') {
            steps {
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                        bash ${DEPLOY_PATH}/fetch-secrets.sh
                    '
                """
            }
        }

        stage('Build FastAPI') {
            when { expression { env.BUILD_FASTAPI == 'true' } }
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}/fastapi-server
                        docker pull ${ECR_REGISTRY}/multiframework-fastapi:latest || true
                        docker build \
                          --cache-from ${ECR_REGISTRY}/multiframework-fastapi:latest \
                          -t ${ECR_REGISTRY}/multiframework-fastapi:${env.GIT_SHA} \
                          -t ${ECR_REGISTRY}/multiframework-fastapi:latest \
                          .
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:${env.GIT_SHA}
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:latest
                    '
                """
            }
        }

        stage('Build Django') {
            when { expression { env.BUILD_DJANGO == 'true' } }
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}/django-server
                        docker pull ${ECR_REGISTRY}/multiframework-django:latest || true
                        docker build \
                          --cache-from ${ECR_REGISTRY}/multiframework-django:latest \
                          -t ${ECR_REGISTRY}/multiframework-django:${env.GIT_SHA} \
                          -t ${ECR_REGISTRY}/multiframework-django:latest \
                          .
                        docker push ${ECR_REGISTRY}/multiframework-django:${env.GIT_SHA}
                        docker push ${ECR_REGISTRY}/multiframework-django:latest
                    '
                """
            }
        }

        stage('Build Node') {
            when { expression { env.BUILD_NODE == 'true' } }
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}/node-server
                        docker pull ${ECR_REGISTRY}/multiframework-node:latest || true
                        docker build \
                          --cache-from ${ECR_REGISTRY}/multiframework-node:latest \
                          -t ${ECR_REGISTRY}/multiframework-node:${env.GIT_SHA} \
                          -t ${ECR_REGISTRY}/multiframework-node:latest \
                          .
                        docker push ${ECR_REGISTRY}/multiframework-node:${env.GIT_SHA}
                        docker push ${ECR_REGISTRY}/multiframework-node:latest
                    '
                """
            }
        }

        stage('Build .NET') {
            when { expression { env.BUILD_DOTNET == 'true' } }
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}/dotnet-server
                        docker pull ${ECR_REGISTRY}/multiframework-dotnet:latest || true
                        docker build \
                          --cache-from ${ECR_REGISTRY}/multiframework-dotnet:latest \
                          -t ${ECR_REGISTRY}/multiframework-dotnet:${env.GIT_SHA} \
                          -t ${ECR_REGISTRY}/multiframework-dotnet:latest \
                          .
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:${env.GIT_SHA}
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:latest
                    '
                """
            }
        }

        stage('DB Migration') {
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}
                        echo "Running DB migrations..."
                        docker run --rm \
                          --network multiframework-login_app-network \
                          --env-file .env \
                          ${ECR_REGISTRY}/multiframework-fastapi:latest \
                          python /app/migrate.py
                        echo "Migration complete."
                    '
                """
            }
        }

        stage('Deploy') {
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}

                        docker-compose pull

                        if [ "${env.BUILD_FASTAPI}" = "true" ]; then
                            docker-compose up -d --no-deps fastapi-backend
                        fi
                        if [ "${env.BUILD_DJANGO}" = "true" ]; then
                            docker-compose up -d --no-deps django-backend
                        fi
                        if [ "${env.BUILD_NODE}" = "true" ]; then
                            docker-compose up -d --no-deps node-backend
                        fi
                        if [ "${env.BUILD_DOTNET}" = "true" ]; then
                            docker-compose up -d --no-deps dotnet-backend
                        fi
                        if [ "${env.CONFIG_CHANGED}" = "true" ]; then
                            docker-compose up -d --no-deps nginx prometheus alertmanager grafana
                        fi

                        docker image prune -f
                    '
                """
            }
        }

        stage('Verify') {
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        sleep 15
                        echo "=== Container Health ==="
                        docker ps --format "table {{.Names}}\\t{{.Status}}"

                        echo ""
                        echo "=== Direct backend checks ==="
                        echo "FastAPI : \$(curl -sf http://localhost:8001/api/health || echo FAILED)"
                        echo "Django  : \$(curl -sf http://localhost:8002/api/health || echo FAILED)"
                        echo "Node    : \$(curl -sf http://localhost:8003/api/health || echo FAILED)"
                        echo ".NET    : \$(curl -sf http://localhost:8004/health     || echo FAILED)"

                        echo ""
                        echo "=== Via CloudFront ==="
                        echo "FastAPI CF: \$(curl -sf http://d3qn5h5of4mccd.cloudfront.net/api/fastapi/health || echo FAILED)"
                        echo "Django CF : \$(curl -sf http://d3qn5h5of4mccd.cloudfront.net/api/django/health  || echo FAILED)"
                        echo "Node CF   : \$(curl -sf http://d3qn5h5of4mccd.cloudfront.net/api/node/health    || echo FAILED)"
                        echo ".NET CF   : \$(curl -sf http://d3qn5h5of4mccd.cloudfront.net/api/dotnet/health  || echo FAILED)"
                    '
                """
            }
        }
    }

    post {
        success { echo "✅ Deployed tag: ${env.GIT_SHA} — CF: http://d3qn5h5of4mccd.cloudfront.net" }
        failure { echo "❌ Failed at tag: ${env.GIT_SHA}" }
    }
}