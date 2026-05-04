pipeline {
    agent any
    
    environment {
        PRIVATE_EC2 = '10.0.11.125'
        DEPLOY_PATH = '/home/ubuntu/multiframework-login'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }
        
        stage('Deploy Backends to EC2') {
            steps {
                echo 'Deploying backends to private EC2...'
                sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${PRIVATE_EC2} '
                        cd ${DEPLOY_PATH}
                        git pull origin main
                        docker-compose down
                        docker-compose build --no-cache
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
            echo '✅ Backends deployed successfully!'
            echo 'Frontend: http://multiframework-frontend-1777874585.s3-website-us-east-1.amazonaws.com'
        }
        failure {
            echo '❌ Deployment failed. Please check the logs.'
        }
    }
}
