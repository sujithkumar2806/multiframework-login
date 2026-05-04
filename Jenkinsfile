pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        ECR_REGISTRY = '608380991635.dkr.ecr.us-east-1.amazonaws.com'
        EC2_BUILDER = '10.0.11.125'
        DEPLOY_PATH = '/home/ubuntu/multiframework-login'
        PREVIOUS_TAG = ''
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }
        
        stage('Get Previous Version') {
            steps {
                echo 'Getting previous deployment version for rollback...'
                sh """
                    ssh ubuntu@${EC2_BUILDER} '
                        cd ${DEPLOY_PATH}
                        # Get current image tag from running containers
                        docker inspect fastapi-backend --format='{{.Config.Image}}' 2>/dev/null | grep -oE ":[0-9]+" | tr -d ":" > /tmp/current_tag.txt || echo "1" > /tmp/current_tag.txt
                    '
                """
            }
        }
        
        stage('Build and Push to ECR') {
            steps {
                echo 'Building and pushing images to ECR...'
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_BUILDER} '
                        cd ${DEPLOY_PATH}
                        
                        # Force reset to latest code
                        git fetch origin
                        git reset --hard origin/main
                        git clean -fd
                        
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        
                        # Get build number (use timestamp if BUILD_NUMBER not available)
                        BUILD_TAG=\${BUILD_NUMBER:-$(date +%Y%m%d%H%M%S)}
                        
                        # Build and push FastAPI
                        cd fastapi-server
                        docker build --no-cache -t multiframework-fastapi:\${BUILD_TAG} .
                        docker tag multiframework-fastapi:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-fastapi:\${BUILD_TAG}
                        docker tag multiframework-fastapi:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-fastapi:latest
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-fastapi:latest
                        cd ..
                        
                        # Build and push Django
                        cd django-server
                        docker build --no-cache -t multiframework-django:\${BUILD_TAG} .
                        docker tag multiframework-django:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-django:\${BUILD_TAG}
                        docker tag multiframework-django:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-django:latest
                        docker push ${ECR_REGISTRY}/multiframework-django:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-django:latest
                        cd ..
                        
                        # Build and push Node.js
                        cd node-server
                        docker build --no-cache -t multiframework-node:\${BUILD_TAG} .
                        docker tag multiframework-node:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-node:\${BUILD_TAG}
                        docker tag multiframework-node:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-node:latest
                        docker push ${ECR_REGISTRY}/multiframework-node:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-node:latest
                        cd ..
                        
                        # Build and push .NET
                        cd dotnet-server
                        docker build --no-cache -t multiframework-dotnet:\${BUILD_TAG} .
                        docker tag multiframework-dotnet:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-dotnet:\${BUILD_TAG}
                        docker tag multiframework-dotnet:\${BUILD_TAG} ${ECR_REGISTRY}/multiframework-dotnet:latest
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:\${BUILD_TAG}
                        docker push ${ECR_REGISTRY}/multiframework-dotnet:latest
                        cd ..
                        
                        # Save current tag for rollback
                        echo "\${BUILD_TAG}" > /tmp/latest_build_tag.txt
                    '
                """
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Deploying with new images...'
                sh """
                    ssh ubuntu@${EC2_BUILDER} '
                        cd ${DEPLOY_PATH}
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
                echo 'Verifying deployment...'
                sh """
                    ssh ubuntu@${EC2_BUILDER} '
                        sleep 15
                        echo "=== Health Checks ==="
                        FASTAPI_HEALTH=\$(curl -s http://localhost/api/fastapi/health)
                        DJANGO_HEALTH=\$(curl -s http://localhost/api/django/health)
                        NODE_HEALTH=\$(curl -s http://localhost/api/node/health)
                        DOTNET_HEALTH=\$(curl -s http://localhost/api/dotnet/health)
                        
                        if [[ "\$FASTAPI_HEALTH" == *"healthy"* ]] && [[ "\$DJANGO_HEALTH" == *"healthy"* ]] && [[ "\$NODE_HEALTH" == *"healthy"* ]] && [[ "\$DOTNET_HEALTH" == *"healthy"* ]]; then
                            echo "✅ All services are healthy!"
                            echo "FastAPI: \$FASTAPI_HEALTH"
                            echo "Django: \$DJANGO_HEALTH"
                            echo "Node.js: \$NODE_HEALTH"
                            echo ".NET: \$DOTNET_HEALTH"
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
            echo "✅ Build and deployment successful!"
            sh """
                ssh ubuntu@${EC2_BUILDER} '
                    echo "Deployment completed at: \$(date)"
                    echo "Images are stored in ECR with version tags"
                '
            """
        }
        failure {
            echo "❌ Deployment failed! Rolling back..."
            script {
                sh """
                    ssh ubuntu@${EC2_BUILDER} '
                        cd ${DEPLOY_PATH}
                        # Get previous tag from backup
                        PREV_TAG=\$(cat /tmp/previous_tag.txt 2>/dev/null || echo "1")
                        
                        if [ "\$PREV_TAG" != "1" ]; then
                            echo "Rolling back to version: \$PREV_TAG"
                            # Pull previous images
                            docker pull ${ECR_REGISTRY}/multiframework-fastapi:\$PREV_TAG
                            docker pull ${ECR_REGISTRY}/multiframework-django:\$PREV_TAG
                            docker pull ${ECR_REGISTRY}/multiframework-node:\$PREV_TAG
                            docker pull ${ECR_REGISTRY}/multiframework-dotnet:\$PREV_TAG
                            
                            # Re-tag as latest
                            docker tag ${ECR_REGISTRY}/multiframework-fastapi:\$PREV_TAG ${ECR_REGISTRY}/multiframework-fastapi:latest
                            docker tag ${ECR_REGISTRY}/multiframework-django:\$PREV_TAG ${ECR_REGISTRY}/multiframework-django:latest
                            docker tag ${ECR_REGISTRY}/multiframework-node:\$PREV_TAG ${ECR_REGISTRY}/multiframework-node:latest
                            docker tag ${ECR_REGISTRY}/multiframework-dotnet:\$PREV_TAG ${ECR_REGISTRY}/multiframework-dotnet:latest
                            
                            # Redeploy
                            docker-compose down
                            docker-compose up -d
                            echo "Rollback completed!"
                        else
                            echo "No previous version found for rollback!"
                        fi
                    '
                """
            }
        }
    }
}
