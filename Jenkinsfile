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
                    env.COMMIT_AUTHOR = sh(script: "git log -1 --format=%an ${env.GIT_COMMIT}", returnStdout: true).trim()
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
                    def exitCode = 0
                    testImage.inside {
                        exitCode = sh(script: 'cd test-scripts && python -m pytest --html=report.html --self-contained-html -v', returnStatus: true)
                    }
                    env.TEST_OUTCOME = (exitCode == 0) ? 'passed' : 'failed'
                    if (exitCode != 0) {
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }

        stage('Publish') {
            steps {
                sh "test -f test-scripts/report.html && cp test-scripts/report.html test-scripts/report-v${env.SCRIPT_VERSION}.html || true"
                publishHTML(target: [
                    reportDir: 'test-scripts',
                    reportFiles: 'report.html',
                    reportName: 'NetTest HTML Report',
                    keepAll: true,
                    alwaysLinkToLastBuild: true,
                    allowMissing: true
                ])
                archiveArtifacts artifacts: "test-scripts/report.html,test-scripts/report-v${env.SCRIPT_VERSION}.html,test-scripts/results/test_results.db", allowEmptyArchive: true
            }
        }

        stage('Change control gate') {
            steps {
                script {
                    if (env.TEST_OUTCOME != 'passed') {
                        env.GATE_OUTCOME = 'skipped'
                        env.GATE_REASON = 'tests did not pass'
                        echo "Skipping change control gate: tests did not pass"
                    } else {
                        withCredentials([string(credentialsId: 'github-pat', variable: 'GITHUB_TOKEN')]) {
                            def exitCode = sh(script: 'bash scripts/check_change_control.sh > gate_output.txt 2>&1', returnStatus: true)
                            def output = readFile('gate_output.txt').trim()
                            echo output
                            if (exitCode == 0) {
                                env.GATE_OUTCOME = 'promoted'
                                env.GATE_REASON = ''
                            } else {
                                env.GATE_OUTCOME = 'rejected'
                                env.GATE_REASON = output.readLines().find { it.startsWith('REJECTED') } ?: 'unknown reason'
                                currentBuild.result = 'FAILURE'
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (binding.hasVariable('testImage') && testImage != null) {
                    env.TEST_OUTCOME = env.TEST_OUTCOME ?: 'unknown'
                    env.GATE_OUTCOME = env.GATE_OUTCOME ?: 'not_evaluated'
                    env.GATE_REASON = env.GATE_REASON ?: ''
                    testImage.inside {
                        sh 'python3 audit/audit_log.py'
                    }
                }
                sh "docker rmi jenky-test-runner:${env.BUILD_NUMBER} || true"
            }
        }
    }
}
