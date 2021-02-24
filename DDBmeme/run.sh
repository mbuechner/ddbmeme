#!/bin/bash

# Start the memegen process
cd /home/memegen
pipenv run gunicorn app.views:app --bind 0.0.0.0:${PORT:-5000} --worker-class uvicorn.workers.UvicornWorker --max-requests=${MAX_REQUESTS:-0} --max-requests-jitter=${MAX_REQUESTS_JITTER:-0} &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start memegen process: $status"
  exit $status
fi

# Start the DDBmeme process
cd /home/DDBmeme
pipenv run python3 manage.py migrate
pipenv run python3 manage.py runserver 0.0.0.0:8080 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start DDBmeme process: $status"
  exit $status
fi

while sleep 60; do
  ps aux |grep memegen |grep -v grep
  PROCESS_1_STATUS=$?
  ps aux |grep DDBmem |grep -v grep
  PROCESS_2_STATUS=$?
  if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
    echo "One of the processes has already exited."
    exit 1
  fi
done
