#!/bin/bash

# Start the memegen process
cd /home/memegen
pipenv run python manage.py runserver --host 127.0.0.1 --port 5000 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start memegen process: $status"
  exit $status
fi

# Start the DDBmeme process
cd /home/DDBmeme
python manage.py runserver 0.0.0.0:80 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start DDBmeme process: $status"
  exit $status
fi

while sleep 60; do
  ps aux |grep 127.0.0.1 |grep -v grep
  PROCESS_1_STATUS=$?
  ps aux |grep 0.0.0.0 |grep -v grep
  PROCESS_2_STATUS=$?
  # If the greps above find anything, they exit with 0 status
  # If they are not both 0, then something is wrong
  if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
    echo "One of the processes has already exited."
    exit 1
  fi
done