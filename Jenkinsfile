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
        
        stage('Build, Push and Deploy on EC2') {
            steps {
                echo 'Building images, pushing to ECR, and deploying on EC2...'
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${PRIVATE_EC2} '
                        cd ${DEPLOY_PATH}
                        git pull origin main
                        
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        
                        # Build FastAPI
                        cd fastapi-server
                        docker build -t multiframework-fastapi:${IMAGE_TAG} .
                        docker tag multiframework-fastapi:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-fastapi:${IMAGE_TAG}
                        docker tag multiframework-fastapi:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-fastapi:latest
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:latest
                        cd ..
                        
                        # Build Django
                        cd django-server
                        docker build -t multiframework-django:${IMAGE_TAG} .
                        docker tag multiframework-django:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-django:${IMAGE_TAG}
                        docker tag multiframework-django:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-django:latest
                        docker push ${ECR_REGISTRY}/multiframework-django:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-django:latest
                        cd ..
                        
                        # Build Node.js
                        cd node-server
                        docker build -t multiframework-node:${IMAGE_TAG} .
                        docker tag multiframework-node:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-node:${IMAGE_TAG}
                        docker tag multiframework-node:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-node:latest
                        docker push ${ECR_REGISTRY}/multiframework-node:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-node:latest
                        cd ..
                        
                        # Build .NET
                        cd dotnet-server
                        docker build -t multiframework-dotnet:${IMAGE_TAG} .
                        docker tag multiframework-dotnet:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-dotnet:${IMAGE_TAG}
                        docker tag multiframework-dotnet:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-dotnet:latest
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:latest
                        cd ..
                        
                        # Deploy with docker-compose
                        docker-compose down
                        docker-compose pull
                        docker-compose up -d
                        docker restart nginx-api 2>/dev/null || true
                    '
                """
            }
        }
        
        stage('Verify') {
            steps {
                sh """
                    ssh ubuntu@${PRIVATE_EC2} '
                        sleep 10
                        echo "FastAPI:"
                        curl -s http://localhost/api/fastapi/health
                        echo ""
                        echo "Django:"
                        curl -s http://localhost/api/django/health
                        echo ""
                        echo "Node.js:"
                        curl -s http://localhost/api/node/health
                        echo ""
                        echo ".NET:"
                        curl -s http://localhost/api/dotnet/health
                        echo ""
                    '
                """
            }
        }
    }
    
    post {
        success {
            echo "✅ Build and deployment successful! New images pushed to ECR with tag: ${IMAGE_TAG}"
        }
        failure {
            echo '❌ Deployment failed. Please check the logs.'
        }
    }
}
