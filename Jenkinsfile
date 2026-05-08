pipeline {
    agent any

    environment {
        AWS_REGION   = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        ECR_REPO     = '608380991635.dkr.ecr.us-east-1.amazonaws.com/multiframework'
        EC2_HOST     = '10.0.11.125'
        DEPLOY_PATH  = '/home/ubuntu/multiframework-login'
        BUILD_NUM    = "${env.BUILD_NUMBER}"
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
                    def changed = sh(
                        script: "git diff --name-only HEAD~1 HEAD 2>/dev/null || echo 'all'",
                        returnStdout: true
                    ).trim()

                    echo "Build #${BUILD_NUM}"
                    echo "Changed:\n${changed}"

                    env.BUILD_FASTAPI  = (changed.contains('fastapi-server/')  || changed == 'all') ? 'true' : 'false'
                    env.BUILD_DJANGO   = (changed.contains('django-server/')   || changed == 'all') ? 'true' : 'false'
                    env.BUILD_NODE     = (changed.contains('node-server/')     || changed == 'all') ? 'true' : 'false'
                    env.BUILD_DOTNET   = (changed.contains('dotnet-server/')   || changed == 'all') ? 'true' : 'false'
                    env.CONFIG_CHANGED = (changed.contains('nginx-api.conf')   ||
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
                        git clean -fd --exclude=.env
                        aws ecr get-login-password --region ${AWS_REGION} \
                          | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    '
                """
            }
        }

        stage('Load Secrets') {
            steps {
                sh "ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} 'bash ${DEPLOY_PATH}/fetch-secrets.sh'"
            }
        }

        stage('Build FastAPI') {
            when { expression { env.BUILD_FASTAPI == 'true' } }
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}/fastapi-server
                        docker build \
                          -t ${ECR_REPO}:fastapi-${BUILD_NUM} \
                          -t ${ECR_REPO}:fastapi-latest \
                          .
                        docker push ${ECR_REPO}:fastapi-${BUILD_NUM}
                        docker push ${ECR_REPO}:fastapi-latest
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
                        docker build \
                          -t ${ECR_REPO}:django-${BUILD_NUM} \
                          -t ${ECR_REPO}:django-latest \
                          .
                        docker push ${ECR_REPO}:django-${BUILD_NUM}
                        docker push ${ECR_REPO}:django-latest
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
                        docker build \
                          -t ${ECR_REPO}:node-${BUILD_NUM} \
                          -t ${ECR_REPO}:node-latest \
                          .
                        docker push ${ECR_REPO}:node-${BUILD_NUM}
                        docker push ${ECR_REPO}:node-latest
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
                        docker build \
                          -t ${ECR_REPO}:dotnet-${BUILD_NUM} \
                          -t ${ECR_REPO}:dotnet-latest \
                          .
                        docker push ${ECR_REPO}:dotnet-${BUILD_NUM}
                        docker push ${ECR_REPO}:dotnet-latest
                    '
                """
            }
        }

        stage('DB Migration') {
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}
                        docker run --rm \
                          --network multiframework-login_app-network \
                          --env-file .env \
                          ${ECR_REPO}:fastapi-latest \
                          python /app/migrate.py
                    '
                """
            }
        }

        stage('Deploy') {
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}

                        # Update docker-compose to use new single repo tags
                        export FASTAPI_IMAGE=${ECR_REPO}:fastapi-latest
                        export DJANGO_IMAGE=${ECR_REPO}:django-latest
                        export NODE_IMAGE=${ECR_REPO}:node-latest
                        export DOTNET_IMAGE=${ECR_REPO}:dotnet-latest

                        docker-compose pull 2>/dev/null || true
                        docker-compose up -d

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
                        echo "=== Build #${BUILD_NUM} ==="
                        docker ps --format "table {{.Names}}\\t{{.Status}}"
                        echo ""
                        echo "FastAPI : \$(curl -sf http://localhost:8001/api/health || echo FAILED)"
                        echo "Django  : \$(curl -sf http://localhost:8002/api/health || echo FAILED)"
                        echo "Node    : \$(curl -sf http://localhost:8003/api/health || echo FAILED)"
                        echo ".NET    : \$(curl -sf http://localhost:8004/health     || echo FAILED)"
                    '
                """
            }
        }
    }

    post {
        success { echo "✅ Build #${BUILD_NUM} deployed!" }
        failure { echo "❌ Build #${BUILD_NUM} failed!" }
    }
}
