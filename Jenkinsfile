pipeline {
    agent any

    triggers {
        // 기존 Jenkins Job과 동일한 polling 주기로 조정한다.
        pollSCM('H/5 * * * *')
    }

    options {
        disableConcurrentBuilds()
        timestamps()
        skipDefaultCheckout()
    }

    parameters {
        string(
            name: 'GIT_REPOSITORY_SSH_URL',
            defaultValue: '',
            description: '최초 배포 시에만 입력합니다. 예: git@github.com:owner/smartdrain.git'
        )
        booleanParam(
            name: 'SEED_MOCK_DATA',
            defaultValue: false,
            description: '최초 배포에서만 실행합니다. 기존 drain_code 데이터는 수정하지 않고 건너뜁니다.'
        )
    }

    environment {
        DEPLOY_DIR = '/deploy/smart-drain'
        DEPLOY_BRANCH = 'develop'
        COMPOSE_PROJECT_NAME = 'smartdrain-dev'
        GIT_CREDENTIAL_ID = 'smartdrain-github-deploy-key'
    }

    stages {
        stage('Preflight') {
            steps {
                sh '.jenkins/scripts/preflight.sh'
            }
        }

        stage('Sync deployment source') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: "${GIT_CREDENTIAL_ID}",
                    keyFileVariable: 'GIT_SSH_KEY',
                    usernameVariable: 'GIT_SSH_USER'
                )]) {
                    sh '.jenkins/scripts/sync-deployment-source.sh'
                }
            }
        }

        stage('Validate') {
            steps {
                sh '.jenkins/scripts/validate.sh'
            }
        }

        stage('Deploy') {
            steps {
                sh '.jenkins/scripts/deploy.sh'
            }
        }

        stage('Optional initial seed') {
            when {
                expression { return params.SEED_MOCK_DATA }
            }
            steps {
                sh '.jenkins/scripts/seed.sh'
            }
        }

        stage('Smoke test') {
            steps {
                sh '.jenkins/scripts/smoke-test.sh'
            }
        }
    }

    post {
        failure {
            sh '.jenkins/scripts/collect-logs.sh || true'
        }
    }
}
