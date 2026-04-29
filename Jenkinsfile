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
        
        stage('Deploy to EC2') {
            steps {
                echo 'Deploying to private EC2...'
                sh """
                    ssh ubuntu@${PRIVATE_EC2} '
                        cd ${DEPLOY_PATH}
                        git pull origin main
                        docker-compose down
                        docker-compose build --no-cache
                        docker-compose up -d
                    '
                """
            }
        }
        
        stage('Verify Deployment') {
            steps {
                echo 'Verifying deployment...'
                sh """
                    ssh ubuntu@${PRIVATE_EC2} '
                        sleep 10
                        docker ps --format "table {{.Names}}\t{{.Status}}"
                        curl -s http://localhost | grep -q "backend-selector" && echo "✅ New frontend deployed" || echo "⚠️ Old frontend still present"
                    '
                """
            }
        }
    }
    
    post {
        success {
            echo '✅ Application deployed successfully!'
            echo 'Access at: http://multiframework-alb-1441586806.us-east-1.elb.amazonaws.com'
        }
        failure {
            echo '❌ Deployment failed. Please check the logs.'
        }
    }
}
