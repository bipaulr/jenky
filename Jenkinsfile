pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SCRIPT_VERSION = readFile('test-scripts/VERSION.txt').trim()
                    currentBuild.displayName = "#${env.BUILD_NUMBER} (test-scripts v${env.SCRIPT_VERSION})"
                }
            }
        }

        stage('Build test-runner image') {
            steps {
                script {
                    testImage = docker.build("jenky-test-runner:${env.BUILD_NUMBER}", "-f docker/Dockerfile.test-runner .")
                }
            }
        }

        stage('Provision environment') {
            steps {
                script {
                    testImage.inside {
                        sh 'bash scripts/setup.sh'
                    }
                }
            }
        }

        stage('Run tests') {
            steps {
                script {
                    testImage.inside {
                        sh 'cd test-scripts && python -m pytest --html=report.html --self-contained-html -v'
                    }
                }
            }
        }

        stage('Publish') {
            steps {
                sh "cp test-scripts/report.html test-scripts/report-v${env.SCRIPT_VERSION}.html"
                publishHTML(target: [
                    reportDir: 'test-scripts',
                    reportFiles: 'report.html',
                    reportName: 'NetTest HTML Report',
                    keepAll: true,
                    alwaysLinkToLastBuild: true,
                    allowMissing: false
                ])
                archiveArtifacts artifacts: "test-scripts/report.html,test-scripts/report-v${env.SCRIPT_VERSION}.html,test-scripts/results/test_results.db", allowEmptyArchive: false
            }
        }

        stage('Change control gate') {
            steps {
                withCredentials([string(credentialsId: 'github-pat', variable: 'GITHUB_TOKEN')]) {
                    sh 'bash scripts/check_change_control.sh'
                }
            }
        }
    }

    post {
        always {
            sh "docker rmi jenky-test-runner:${env.BUILD_NUMBER} || true"
        }
    }
}
