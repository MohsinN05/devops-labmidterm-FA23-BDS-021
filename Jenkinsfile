pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        IMAGE_NAME = 'midterm-api'
        CONTAINER_NAME = 'midterm-api'
        DOCKERHUB_IMAGE = 'mohsinn05/midterm-api'
        STUDENT_ID = 'FA23-BDS-021'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        PYTHONDONTWRITEBYTECODE = '1'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    echo "Checked out commit: $GIT_COMMIT"
                    echo "Branch: $BRANCH_NAME"
                    test -f config.json
                    test -f dataset/train.csv
                    test -f train.py
                    test -f app.py
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    python3 -m venv .venv-ci
                    .venv-ci/bin/python -m pip install --upgrade pip
                    .venv-ci/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Train Model') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    GIT_COMMIT="$GIT_COMMIT" .venv-ci/bin/python train.py

                    echo "Generated model artifacts:"
                    ls -lh artifacts/
                    test -f artifacts/model.joblib
                    test -f artifacts/metrics.json
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    .venv-ci/bin/python -m unittest discover -s tests -v
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    docker build \
                        -t "$IMAGE_NAME:$BUILD_NUMBER" \
                        -t "$IMAGE_NAME:latest" .
                '''
            }
        }

        stage('Deploy API') {
            steps {
                sh '''#!/usr/bin/env bash
                    set -euo pipefail

                    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

                    docker run -d \
                        --name "$CONTAINER_NAME" \
                        --restart unless-stopped \
                        -p 8000:8000 \
                        "$IMAGE_NAME:$BUILD_NUMBER"

                    echo "Waiting for API to become healthy..."

                    for attempt in $(seq 1 30); do
                        if curl -fsS http://127.0.0.1:8000/health; then
                            echo
                            break
                        fi

                        if [ "$attempt" -eq 30 ]; then
                            echo "API did not become healthy."
                            docker logs "$CONTAINER_NAME" || true
                            exit 1
                        fi

                        sleep 2
                    done

                    echo "Checking deployed metrics..."
                    curl -fsS http://127.0.0.1:8000/metrics \
                        -o /tmp/midterm-metrics.json

                    .venv-ci/bin/python -c '
import json
with open("/tmp/midterm-metrics.json") as f:
    metrics = json.load(f)

required = ["student_id", "accuracy", "training_rows",
            "model_version", "git_sha"]

missing = [key for key in required if key not in metrics]
if missing:
    raise SystemExit(f"Missing metrics fields: {missing}")

if metrics["student_id"] != "FA23-BDS-021":
    raise SystemExit(f"Unexpected student ID: {metrics['student_id']}")

print(json.dumps(metrics, indent=2))
'
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully.'
            script {
                if (env.MIDTERM_SENDER_EMAIL?.trim()) {
                    emailext(
                        from: env.MIDTERM_SENDER_EMAIL,
                        to: 'qasimalik@gmail.com',
                        subject: "CSC418 DevOps Midterm - FA23-BDS-021 - SUCCESS",
                        body: """The ML retraining and deployment pipeline succeeded.

Student ID: FA23-BDS-021
Build: ${env.BUILD_NUMBER}
Commit: ${env.GIT_COMMIT}
Build URL: ${env.BUILD_URL}

The API has been deployed and its health and metrics endpoints verified."""
                    )
                } else {
                    echo 'Email not sent yet: configure MIDTERM_SENDER_EMAIL and SMTP before the final run.'
                }
            }
        }

        failure {
            echo 'Pipeline failed. Inspect the failed stage in the Jenkins console output.'
        }
    }
}
