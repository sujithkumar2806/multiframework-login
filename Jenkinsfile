pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from Git...'
                checkout scm
            }
        }
        
        stage('Build Docker Images') {
            parallel {
                stage('Build FastAPI') {
                    steps {
                        dir('fastapi-server') {
                            sh 'docker build -t multiframework-fastapi:${DOCKER_IMAGE_TAG} .'
                        }
                    }
                }
                stage('Build Django') {
                    steps {
                        dir('django-server') {
                            sh 'docker build -t multiframework-django:${DOCKER_IMAGE_TAG} .'
                        }
                    }
                }
                stage('Build Node') {
                    steps {
                        dir('node-server') {
                            sh 'docker build -t multiframework-node:${DOCKER_IMAGE_TAG} .'
                        }
                    }
                }
                stage('Build .NET') {
                    steps {
                        dir('dotnet-server') {
                            sh 'docker build -t multiframework-dotnet:${DOCKER_IMAGE_TAG} .'
                        }
                    }
                }
                stage('Build Frontend') {
                    steps {
                        dir('frontend') {
                            sh 'docker build -t multiframework-frontend:${DOCKER_IMAGE_TAG} .'
                        }
                    }
                }
                stage('Build Nginx') {
                    steps {
                        dir('nginx') {
                            sh 'docker build -t multiframework-nginx:${DOCKER_IMAGE_TAG} .'
                        }
                    }
                }
            }
        }
        
        stage('Push to ECR') {
            steps {
                script {
                    sh '''
                        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
                        
                        # Tag and push all images
                        docker tag multiframework-fastapi:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-fastapi:${DOCKER_IMAGE_TAG}
                        docker tag multiframework-fastapi:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-fastapi:latest
                        docker push $ECR_REGISTRY/multiframework-fastapi:${DOCKER_IMAGE_TAG}
                        docker push $ECR_REGISTRY/multiframework-fastapi:latest
                        
                        docker tag multiframework-django:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-django:${DOCKER_IMAGE_TAG}
                        docker tag multiframework-django:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-django:latest
                        docker push $ECR_REGISTRY/multiframework-django:${DOCKER_IMAGE_TAG}
                        docker push $ECR_REGISTRY/multiframework-django:latest
                        
                        docker tag multiframework-node:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-node:${DOCKER_IMAGE_TAG}
                        docker tag multiframework-node:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-node:latest
                        docker push $ECR_REGISTRY/multiframework-node:${DOCKER_IMAGE_TAG}
                        docker push $ECR_REGISTRY/multiframework-node:latest
                        
                        docker tag multiframework-dotnet:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-dotnet:${DOCKER_IMAGE_TAG}
                        docker tag multiframework-dotnet:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-dotnet:latest
                        docker push $ECR_REGISTRY/multiframework-dotnet:${DOCKER_IMAGE_TAG}
                        docker push $ECR_REGISTRY/multiframework-dotnet:latest
                        
                        docker tag multiframework-frontend:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-frontend:${DOCKER_IMAGE_TAG}
                        docker tag multiframework-frontend:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-frontend:latest
                        docker push $ECR_REGISTRY/multiframework-frontend:${DOCKER_IMAGE_TAG}
                        docker push $ECR_REGISTRY/multiframework-frontend:latest
                        
                        docker tag multiframework-nginx:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-nginx:${DOCKER_IMAGE_TAG}
                        docker tag multiframework-nginx:${DOCKER_IMAGE_TAG} $ECR_REGISTRY/multiframework-nginx:latest
                        docker push $ECR_REGISTRY/multiframework-nginx:${DOCKER_IMAGE_TAG}
                        docker push $ECR_REGISTRY/multiframework-nginx:latest
                    '''
                }
            }
        }
        
        stage('Deploy to EC2') {
            steps {
                sh '''
                    ssh -o StrictHostKeyChecking=no ubuntu@10.0.11.125 'cd ~/multiframework-login && \
                    docker-compose down && \
                    docker-compose pull && \
                    docker-compose up -d'
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                sh '''
                    sleep 10
                    curl -f http://10.0.11.125:80/ || exit 1
                '''
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline completed'
        }
        success {
            echo 'Build and deployment successful!'
        }
        failure {
            echo 'Build failed!'
        }
    }
}
