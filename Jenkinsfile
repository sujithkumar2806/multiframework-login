pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        PRIVATE_EC2 = '10.0.11.125'
        DEPLOY_PATH = '/home/ubuntu/multiframework-login'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }
        
        stage('Login to ECR') {
            steps {
                script {
                    sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}"
                }
            }
        }
        
        stage('Build and Push Images') {
            parallel {
                stage('Build FastAPI') {
                    steps {
                        dir('fastapi-server') {
                            sh "docker build -t multiframework-fastapi:${IMAGE_TAG} ."
                            sh "docker tag multiframework-fastapi:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-fastapi:${IMAGE_TAG}"
                            sh "docker tag multiframework-fastapi:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-fastapi:latest"
                            sh "docker push ${ECR_REGISTRY}/multiframework-fastapi:${IMAGE_TAG}"
                            sh "docker push ${ECR_REGISTRY}/multiframework-fastapi:latest"
                        }
                    }
                }
                stage('Build Django') {
                    steps {
                        dir('django-server') {
                            sh "docker build -t multiframework-django:${IMAGE_TAG} ."
                            sh "docker tag multiframework-django:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-django:${IMAGE_TAG}"
                            sh "docker tag multiframework-django:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-django:latest"
                            sh "docker push ${ECR_REGISTRY}/multiframework-django:${IMAGE_TAG}"
                            sh "docker push ${ECR_REGISTRY}/multiframework-django:latest"
                        }
                    }
                }
                stage('Build Node') {
                    steps {
                        dir('node-server') {
                            sh "docker build -t multiframework-node:${IMAGE_TAG} ."
                            sh "docker tag multiframework-node:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-node:${IMAGE_TAG}"
                            sh "docker tag multiframework-node:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-node:latest"
                            sh "docker push ${ECR_REGISTRY}/multiframework-node:${IMAGE_TAG}"
                            sh "docker push ${ECR_REGISTRY}/multiframework-node:latest"
                        }
                    }
                }
                stage('Build .NET') {
                    steps {
                        dir('dotnet-server') {
                            sh "docker build -t multiframework-dotnet:${IMAGE_TAG} ."
                            sh "docker tag multiframework-dotnet:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-dotnet:${IMAGE_TAG}"
                            sh "docker tag multiframework-dotnet:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-dotnet:latest"
                            sh "docker push ${ECR_REGISTRY}/multiframework-dotnet:${IMAGE_TAG}"
                            sh "docker push ${ECR_REGISTRY}/multiframework-dotnet:latest"
                        }
                    }
                }
            }
        }
        
        stage('Deploy to EC2') {
            steps {
                echo 'Deploying backends to private EC2...'
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${PRIVATE_EC2} '
                        cd ${DEPLOY_PATH}
                        git pull origin main
                        docker-compose down
                        docker-compose pull
                        docker-compose up -d
                        docker restart nginx-api 2>/dev/null || echo "nginx-api not running"
                    '
                """
            }
        }
        
        stage('Verify Backends') {
            steps {
                echo 'Verifying backends...'
                sh """
                    ssh ubuntu@${PRIVATE_EC2} '
                        sleep 5
                        curl -s http://localhost/api/fastapi/health && echo ""
                        curl -s http://localhost/api/django/health && echo ""
                        curl -s http://localhost/api/node/health && echo ""
                        curl -s http://localhost/api/dotnet/health && echo ""
                    '
                """
            }
        }
    }
    
    post {
        success {
            echo '✅ Build and deployment successful!'
            echo "Images pushed to ECR with tag: ${IMAGE_TAG}"
        }
        failure {
            echo '❌ Deployment failed. Please check the logs.'
        }
    }
}
