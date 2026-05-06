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

        // ── STAGE 1: figure out what changed and set the image tag ──────────
        stage('Detect changes') {
            steps {
                script {
                    // Git SHA is the image tag — short, unique, traceable
                    env.GIT_SHA = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()

                    // What files changed between this commit and the previous one?
                    // On first-ever build HEAD~1 doesn't exist, so fall back to 'all'
                    def changed = sh(
                        script: """
                            git diff --name-only HEAD~1 HEAD 2>/dev/null || echo 'all'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Git SHA (image tag): ${env.GIT_SHA}"
                    echo "Changed files:\n${changed}"

                    // Set a flag for each service
                    env.BUILD_FASTAPI = (changed.contains('fastapi-server/') || changed == 'all') ? 'true' : 'false'
                    env.BUILD_DJANGO  = (changed.contains('django-server/')  || changed == 'all') ? 'true' : 'false'
                    env.BUILD_NODE    = (changed.contains('node-server/')    || changed == 'all') ? 'true' : 'false'
                    env.BUILD_DOTNET  = (changed.contains('dotnet-server/')  || changed == 'all') ? 'true' : 'false'
                    // Also rebuild if shared files changed (nginx config, docker-compose, etc.)
                    env.CONFIG_CHANGED = (changed.contains('nginx') || changed.contains('docker-compose') || changed.contains('prometheus.yml')) ? 'true' : 'false'

                    echo "Builds: fastapi=${env.BUILD_FASTAPI} django=${env.BUILD_DJANGO} node=${env.BUILD_NODE} dotnet=${env.BUILD_DOTNET}"
                }
            }
        }

        // ── STAGE 2: sync code + ECR login on EC2 ───────────────────────────
        stage('Sync code on EC2') {
            steps {
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}
                        git fetch origin
                        git reset --hard origin/main
                        git clean -fd

                        aws ecr get-login-password --region ${AWS_REGION} \
                          | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    '
                """
            }
        }

        // ── STAGE 3: build + push only what changed ──────────────────────────
        stage('Build FastAPI') {
            when { expression { env.BUILD_FASTAPI == 'true' } }
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}/fastapi-server

                        # Pull latest for layer cache
                        docker pull ${ECR_REGISTRY}/multiframework-fastapi:latest || true

                        # Build with both the SHA tag and latest
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

        // ── STAGE 4: DB migration (always runs before deploy) ───────────────
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
        stage('Load Secrets') {
            steps   {
                sh """
                ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                bash ${DEPLOY_PATH}/fetch-secrets.sh
            '
        """
            }
        }

        // ── STAGE 5: deploy only changed services ────────────────────────────
        stage('Deploy') {
            steps {
                sh """
                    ssh ubuntu@${EC2_HOST} '
                        cd ${DEPLOY_PATH}

                        # Pull updated images (skips instantly if digest unchanged)
                        docker-compose pull

                        # Restart only services whose image was rebuilt
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
                            docker-compose up -d --no-deps nginx
                        fi

                        # Prune only dangling images - never prune build cache
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
        success { echo "Deployed image tag: ${env.GIT_SHA}" }
        failure { echo "Deployment failed at tag: ${env.GIT_SHA}" }
    }
}