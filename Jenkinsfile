pipeline {
  agent any
  stages {
    stage('Convert JSONL to CSV') {
      steps {
        script {
          sh 'python3 /home/sharath/Downloads/INDIA.py /home/sharath/Downloads/MIMS India output.csv'
        }

      }
    }

  }
}