pipeline {
    agent { label 'windows' }

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        MONGO_URI = ''
        MONGO_DATABASE = 'dataflow_test'
        PYTHONUTF8 = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Set Up Python') {
            steps {
                bat '''
                    @echo off
                    py -3.11 --version
                    if errorlevel 1 exit /b 1

                    py -3.11 -m venv .venv-ci
                    if errorlevel 1 exit /b 1

                    .venv-ci\\Scripts\\python.exe -m pip install --upgrade pip
                    if errorlevel 1 exit /b 1

                    .venv-ci\\Scripts\\python.exe -m pip install -r requirements.txt
                    if errorlevel 1 exit /b 1

                    if not exist reports mkdir reports
                '''
            }
        }

        stage('Lint') {
            steps {
                bat '''
                    .venv-ci\\Scripts\\python.exe -m ruff check app tests qa scripts
                '''
            }
        }

        stage('Backend Tests and Coverage') {
            steps {
                bat '''
                    @echo off
                    set "MONGO_URI="
                    set "PYTHONPATH=%CD%"

                    .venv-ci\\Scripts\\python.exe -m pytest tests -ra --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:reports/coverage.xml --junitxml=reports/test-results.xml
                '''
            }
        }

        stage('Prepare Browser Tests') {
            steps {
                bat '''
                    @echo off
                    set "MONGO_URI="
                    set "PYTHONPATH=%CD%"

                    .venv-ci\\Scripts\\python.exe -m playwright install chromium
                    if errorlevel 1 exit /b 1

                    .venv-ci\\Scripts\\python.exe scripts/load_data.py --data-dir data/sample --db data/ui-test.sqlite
                    if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Browser Tests') {
            steps {
                bat '''
                    @echo off
                    set "MONGO_URI="
                    set "PYTHONPATH=%CD%"

                    .venv-ci\\Scripts\\python.exe -m pytest qa/test_dashboard.py -v --junitxml=reports/ui-test-results.xml
                '''
            }
        }
    }

    post {
        always {
            junit(
                testResults: 'reports/*test-results.xml',
                allowEmptyResults: true
            )

            archiveArtifacts(
                artifacts: 'reports/**,htmlcov/**',
                allowEmptyArchive: true
            )
        }
    }
}