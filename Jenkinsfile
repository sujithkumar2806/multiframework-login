pipeline {
    agent any

    parameters {
        string(
            name: 'ROLLBACK_BUILD',
            defaultValue: '',
            description: 'Enter build number to rollback (e.g. 44). Leave empty for new build.'
        )
    }

    environment {
        AWS_REGION   = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        ECR_REPO     = '608380991635.dkr.ecr.us-east-1.amazonaws.com/multiframework'
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
                    def changed = sh(
                        script: "git diff --name-only HEAD~1 HEAD 2>/dev/null || echo 'all'",
                        returnStdout: true
                    ).trim()

                    echo "Changed files:\n${changed}"
                    env.BUILD_FASTAPI  = 'true'
                    env.BUILD_DJANGO   = 'true'
                    env.BUILD_NODE     = 'true'
                    env.BUILD_DOTNET   = 'true'

                    // env.BUILD_FASTAPI  = (changed.contains('fastapi-server/')  || changed == 'all') ? 'true' : 'false'
                    // env.BUILD_DJANGO   = (changed.contains('django-server/')   || changed == 'all') ? 'true' : 'false'
                    // env.BUILD_NODE     = (changed.contains('node-server/')     || changed == 'all') ? 'true' : 'false'
                    // env.BUILD_DOTNET   = (changed.contains('dotnet-server/')   || changed == 'all') ? 'true' : 'false'
                }
            }
        }

        stage('Set Build Version') {
            steps {
                script {
                    if (params.ROLLBACK_BUILD?.trim()) {
                        env.BUILD_VERSION = params.ROLLBACK_BUILD.trim()
                        env.IS_ROLLBACK = "true"
                    } else {
                        env.BUILD_VERSION = env.BUILD_NUMBER
                        env.IS_ROLLBACK = "false"
                    }

                    echo "Using BUILD_VERSION = ${env.BUILD_VERSION}"
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

        stage('Build Images') {
            steps {
                script {

                    def buildService = { dir, name ->
                        sh """
                            ssh ubuntu@${EC2_HOST} '
                                cd ${DEPLOY_PATH}/${dir}
                                docker build -t ${ECR_REPO}:${name}-${BUILD_VERSION} .
                                docker push ${ECR_REPO}:${name}-${BUILD_VERSION}
                            '
                        """
                    }


                    

                    if (env.BUILD_FASTAPI == 'true') buildService('fastapi-server', 'fastapi')
                    if (env.BUILD_DJANGO == 'true')  buildService('django-server', 'django')
                    if (env.BUILD_NODE == 'true')    buildService('node-server', 'node')
                    if (env.BUILD_DOTNET == 'true')  buildService('dotnet-server', 'dotnet')
                }
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
                          ${ECR_REPO}:fastapi-${BUILD_VERSION} \
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

                        export BUILD_VERSION=${BUILD_VERSION}
                        export ECR_REPO=${ECR_REPO}


                        docker-compose down
                        docker-compose pull
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
                        echo "=== Deployment Build: ${BUILD_VERSION} ==="
                        docker ps --format "table {{.Names}}\\t{{.Status}}"
                        echo ""
                        echo "FastAPI : \$(curl -sf http://localhost:8001/api/health || echo FAILED)"
                        echo "Django  : \$(curl -sf http://localhost:8002/api/health || echo FAILED)"
                        echo "Node    : \$(curl -sf http://localhost:8003/api/health || echo FAILED)"
                        echo ".NET    : \$(curl -sf http://localhost:8004/health || echo FAILED)"
                    '
                """
            }
        }
    }

    post {
        success {
            echo "✅ Build ${BUILD_VERSION} deployed successfully"
        }
        failure {
            echo "❌ Build ${BUILD_VERSION} failed"
        }
    }
}