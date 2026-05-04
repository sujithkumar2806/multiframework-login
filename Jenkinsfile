pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        EC2_BUILDER = '10.0.11.125'
        DEPLOY_PATH = '/home/ubuntu/multiframework-login'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }
        
        stage('Build and Deploy on EC2') {
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
                        
                        # Get timestamp for versioning
                        BUILD_TAG=\$(date +%Y%m%d%H%M%S)
                        
                        # Build and push FastAPI
                        echo "Building FastAPI..."
                        cd fastapi-server
                        docker build --no-cache -t multiframework-fastapi:\${BUILD_TAG} .
                        docker tag multiframework-fastapi:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-fastapi:\${BUILD_TAG}
                        docker tag multiframework-fastapi:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-fastapi:latest
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:latest
                        cd ..
                        
                        # Build and push Django
                        echo "Building Django..."
                        cd django-server
                        docker build --no-cache -t multiframework-django:\${BUILD_TAG} .
                        docker tag multiframework-django:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-django:\${BUILD_TAG}
                        docker tag multiframework-django:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-django:latest
                        docker push ${ECR_REGISTRY}/multiframework-django:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-django:latest
                        cd ..
                        
                        # Build and push Node.js
                        echo "Building Node.js..."
                        cd node-server
                        docker build --no-cache -t multiframework-node:\${BUILD_TAG} .
                        docker tag multiframework-node:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-node:\${BUILD_TAG}
                        docker tag multiframework-node:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-node:latest
                        docker push ${ECR_REGISTRY}/multiframework-node:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-node:latest
                        cd ..
                        
                        # Build and push .NET
                        echo "Building .NET..."
                        cd dotnet-server
                        docker build --no-cache -t multiframework-dotnet:\${BUILD_TAG} .
                        docker tag multiframework-dotnet:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-dotnet:\${BUILD_TAG}
                        docker tag multiframework-dotnet:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-dotnet:latest
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:latest
                        cd ..
                        
                        # Save build tag for reference
                        echo "\${BUILD_TAG}" > /tmp/latest_build_tag.txt
                        
                        # Deploy with docker-compose
                        echo "Deploying containers..."
                        docker-compose down
                        docker-compose pull
                        docker-compose up -d
                        
                        # Clean up old images
                        docker system prune -f
                    '
                """
            }
        }
        
        stage('Verify') {
            steps {
                echo 'Verifying deployment...'
                sh """
                    ssh ubuntu@${EC2_BUILDER} '
                        sleep 15
                        echo "=== Health Checks ==="
                        
                        FASTAPI_HEALTH=\$(curl -s http://localhost/api/fastapi/health)
                        DJANGO_HEALTH=\$(curl -s http://localhost/api/django/health)
                        NODE_HEALTH=\$(curl -s http://localhost/api/node/health)
                        DOTNET_HEALTH=\$(curl -s http://localhost/api/dotnet/health)
                        
                        echo "FastAPI: \$FASTAPI_HEALTH"
                        echo "Django: \$DJANGO_HEALTH"
                        echo "Node.js: \$NODE_HEALTH"
                        echo ".NET: \$DOTNET_HEALTH"
                        
                        if echo "\$FASTAPI_HEALTH" | grep -q "healthy" && echo "\$DJANGO_HEALTH" | grep -q "healthy" && echo "\$NODE_HEALTH" | grep -q "healthy" && echo "\$DOTNET_HEALTH" | grep -q "healthy"; then
                            echo "✅ All services are healthy!"
                            exit 0
                        else
                            echo "❌ Some services failed health check!"
                            exit 1
                        fi
                    '
                """
            }
        }
    }
    
    post {
        success {
            echo '✅ Build and deployment successful!'
            sh """
                ssh ubuntu@${EC2_BUILDER} '
                    echo "Deployment completed at: \$(date)"
                    echo "Latest build tag: \$(cat /tmp/latest_build_tag.txt 2>/dev/null || echo "unknown")"
                '
            """
        }
        failure {
            echo '❌ Deployment failed!'
            echo 'To rollback, run: ./rollback.sh'
        }
    }
}
