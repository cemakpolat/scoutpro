#!/bin/sh

SERVICE_NAME=Opta-API
PID_PATH_NAME=/tmp/opta-api
MAIN_PATH=src/main.py
PYTHON=python3
PIP=python3

case $1 in
    install)
        echo "Installing required libraries for $SERVICE_NAME ..."
        $PIP install -r requirements.txt
        # $PYTHON setup.py install
        echo "Installed required libraries for $SERVICE_NAME ..."
    ;;
    start)
        echo "Starting $SERVICE_NAME ..."
        if [ ! -f $PID_PATH_NAME ]; then
            nohup $PYTHON $MAIN_PATH /tmp 2>> /dev/null >> /dev/null &
                        echo $! > $PID_PATH_NAME
            echo "$SERVICE_NAME started ..."
        else
            echo "$SERVICE_NAME is already running ..."
        fi
    ;;
    stop)
        if [ -f $PID_PATH_NAME ]; then
            PID=$(cat $PID_PATH_NAME);
            echo "$SERVICE_NAME stoping ..."
            kill $PID;
            echo "$SERVICE_NAME stopped ..."
            rm $PID_PATH_NAME
        else
            echo "$SERVICE_NAME is not running ..."
        fi
    ;;
esac