pipeline {
    agent any

    stages {
        stage('Convert JSONL to CSV') {
            steps {
                script {
                    // Example using python
                    sh 'python3 /home/sharath/Downloads/INDIA.py /home/sharath/Downloads/MIMS India output.csv'
                }
            }
        }
    }
}
