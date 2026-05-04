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
        
        stage('Build and Push to ECR') {
            steps {
                echo 'Building and pushing images to ECR...'
                sh """
                    # Login to ECR
                    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    
                    # Build and push FastAPI
                    cd fastapi-server
                    docker build --no-cache -t multiframework-fastapi:${IMAGE_TAG} .
                    docker tag multiframework-fastapi:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-fastapi:${IMAGE_TAG}
                    docker tag multiframework-fastapi:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-fastapi:latest
                    docker push ${ECR_REGISTRY}/multiframework-fastapi:${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/multiframework-fastapi:latest
                    cd ..
                    
                    # Build and push Django
                    cd django-server
                    docker build --no-cache -t multiframework-django:${IMAGE_TAG} .
                    docker tag multiframework-django:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-django:${IMAGE_TAG}
                    docker tag multiframework-django:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-django:latest
                    docker push ${ECR_REGISTRY}/multiframework-django:${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/multiframework-django:latest
                    cd ..
                    
                    # Build and push Node.js
                    cd node-server
                    docker build --no-cache -t multiframework-node:${IMAGE_TAG} .
                    docker tag multiframework-node:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-node:${IMAGE_TAG}
                    docker tag multiframework-node:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-node:latest
                    docker push ${ECR_REGISTRY}/multiframework-node:${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/multiframework-node:latest
                    cd ..
                    
                    # Build and push .NET
                    cd dotnet-server
                    docker build --no-cache -t multiframework-dotnet:${IMAGE_TAG} .
                    docker tag multiframework-dotnet:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-dotnet:${IMAGE_TAG}
                    docker tag multiframework-dotnet:${IMAGE_TAG} ${ECR_REGISTRY}/multiframework-dotnet:latest
                    docker push ${ECR_REGISTRY}/multiframework-dotnet:${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/multiframework-dotnet:latest
                    cd ..
                """
            }
        }
        
        stage('Deploy to EC2') {
            steps {
                echo 'Deploying to EC2...'
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${PRIVATE_EC2} '
                        # Force reset to latest code
                        cd ${DEPLOY_PATH}
                        git fetch origin
                        git reset --hard origin/main
                        git clean -fd
                        
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        
                        # Pull and restart
                        docker-compose down
                        docker system prune -af
                        docker-compose pull
                        docker-compose up -d
                    '
                """
            }
        }
        
        stage('Verify') {
            steps {
                sh """
                    ssh ubuntu@${PRIVATE_EC2} '
                        sleep 15
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
