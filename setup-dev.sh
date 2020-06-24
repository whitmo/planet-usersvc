#!/bin/bash -ex
tox

echo "tests finished"

docker run -d --name firestore-emulator \
       --env "FIRESTORE_PROJECT_ID=dummy-project-id"  \
       --env "PORT=8080"  \
       --publish 8080:8080 \
       --rm \
       mtlynch/firestore-emulator-docker

echo "emulator running"

export GOOGLE_CLOUD_PROJECT=dummy-firestore-id
export FIRESTORE_EMULATOR_HOST=localhost:8080

./.tox/py37/bin/pserve usersvc.ini
