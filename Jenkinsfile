pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        EC2_BUILDER = '10.0.11.125'
        DEPLOY_PATH = '/home/ubuntu/multiframework-login'
        S3_BUCKET = 'multiframework-frontend-1777874585'
        CLOUDFRONT_ID = 'E2JMOVMJHY8Y6M'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }
        
        stage('Upload Frontend to S3') {
            steps {
                echo 'Uploading frontend files to S3...'
                sh """
                    # Upload frontend files to S3
                    aws s3 cp frontend/index.html s3://${S3_BUCKET}/index.html --content-type "text/html"
                    aws s3 cp frontend/script.js s3://${S3_BUCKET}/script.js --content-type "application/javascript"
                    aws s3 cp frontend/dashboard.html s3://${S3_BUCKET}/dashboard.html --content-type "text/html"
                    
                    # Invalidate CloudFront cache
                    aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_ID} --paths "/*"
                    
                    echo "✅ Frontend deployed to S3 + CloudFront"
                """
            }
        }
        
        stage('Build and Deploy Backend on EC2') {
            steps {
                echo 'Building images on EC2 and pushing to ECR...'
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_BUILDER} '
                        cd ${DEPLOY_PATH}
                        
                        # Force reset to latest code
                        git fetch origin
                        git reset --hard origin/main
                        git clean -fd
                        
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        
                        # Pull latest images for cache
                        docker pull ${ECR_REGISTRY}/multiframework-fastapi:latest || true
                        docker pull ${ECR_REGISTRY}/multiframework-django:latest || true
                        docker pull ${ECR_REGISTRY}/multiframework-node:latest || true
                        docker pull ${ECR_REGISTRY}/multiframework-dotnet:latest || true
                        
                        BUILD_TAG=\$(date +%Y%m%d%H%M%S)
                        
                        # Build and push FastAPI
                        cd fastapi-server
                        docker build -t multiframework-fastapi:\${BUILD_TAG} --cache-from ${ECR_REGISTRY}/multiframework-fastapi:latest .
                        docker tag multiframework-fastapi:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-fastapi:\${BUILD_TAG}
                        docker tag multiframework-fastapi:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-fastapi:latest
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:latest
                        cd ..
                        
                        # Build and push Django
                        cd django-server
                        docker build -t multiframework-django:\${BUILD_TAG} --cache-from ${ECR_REGISTRY}/multiframework-django:latest .
                        docker tag multiframework-django:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-django:\${BUILD_TAG}
                        docker tag multiframework-django:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-django:latest
                        docker push ${ECR_REGISTRY}/multiframework-django:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-django:latest
                        cd ..
                        
                        # Build and push Node.js
                        cd node-server
                        docker build -t multiframework-node:\${BUILD_TAG} --cache-from ${ECR_REGISTRY}/multiframework-node:latest .
                        docker tag multiframework-node:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-node:\${BUILD_TAG}
                        docker tag multiframework-node:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-node:latest
                        docker push ${ECR_REGISTRY}/multiframework-node:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-node:latest
                        cd ..
                        
                        # Build and push .NET
                        cd dotnet-server
                        docker build -t multiframework-dotnet:\${BUILD_TAG} --cache-from ${ECR_REGISTRY}/multiframework-dotnet:latest .
                        docker tag multiframework-dotnet:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-dotnet:\${BUILD_TAG}
                        docker tag multiframework-dotnet:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-dotnet:latest
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:latest
                        cd ..
                        
                        echo "\${BUILD_TAG}" > /tmp/latest_build_tag.txt
                        
                        # Deploy
                        docker-compose down
                        docker-compose pull
                        docker-compose up -d
                        docker system prune -f
                    '
                """
            }
        }
        
        stage('Verify') {
            steps {
                sh """
                    ssh ubuntu@${EC2_BUILDER} '
                        sleep 10
                        echo "FastAPI: \$(curl -s http://localhost/api/fastapi/health)"
                        echo "Django: \$(curl -s http://localhost/api/django/health)"
                        echo "Node.js: \$(curl -s http://localhost/api/node/health)"
                        echo ".NET: \$(curl -s http://localhost/api/dotnet/health)"
                    '
                """
            }
        }
    }
    
    post {
        success {
            echo '✅ Full deployment successful! Frontend + Backend updated.'
        }
        failure {
            echo '❌ Deployment failed!'
        }
    }
}
