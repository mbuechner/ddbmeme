#!/bin/bash

# Start the memegen process
cd /home/memegen || exit
pipenv run gunicorn app.views:app --bind 0.0.0.0:5000 --worker-class uvicorn.workers.UvicornWorker --max-requests=0 --max-requests-jitter=0 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start memegen process: $status"
  exit $status
fi

# Start the DDBmeme process
cd /home/DDBmeme || exit
# pipenv run python3 manage.py migrate
pipenv run python3 manage.py runserver 0.0.0.0:8080 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start DDBmeme process: $status"
  exit $status
fi

while true; do
  sleep 300
  pgrep -f memegen > /dev/null 2>&1
  PROCESS_1_STATUS=$?
  pgrep -f DDBmeme > /dev/null 2>&1
  PROCESS_2_STATUS=$?
  if [ $PROCESS_1_STATUS -ne 0 ] || [ $PROCESS_2_STATUS -ne 0 ]; then
    echo "One of the processes has already exited."
    exit 1
  fi
done
