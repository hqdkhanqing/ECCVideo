#!/bin/sh
# wait-for-forward-and-source-port.sh

set -e
cmd="$@"

# if   [ -z $ECCI_MONITOR_SOURCE_PORT ];
# then 
#     echo   "no ECCI_MONITOR_SOURCE_PORT "
#     exit
# fi

# if   [ -z $ECCI_MONITOR_FORWARD_PORT ];
# then 
#     echo   "no ECCI_MONITOR_FORWARD_PORT "
#     exit
# fi


if [[ "$ECCI_MONITOR_MODE" == "user" ]];
then
    if [[ -z "$ECCI_MONITOR_SOURCE_IP" ]]; 
    then
        echo "error: The IP of the subscribing mqtt needs to be provided"
        exit $1
    fi

    if [[ -z $ECCI_MONITOR_SOURCE_PORT ]];
    then
        echo "error: The PORT of the subscribing mqtt needs to be provided"
        exit $1
    fi

    if [[ -z $ECCI_MONTTOR_SOURCE_USERNAME ]];
    then
        export ECCI_MONTTOR_SOURCE_USERNAME="dashboard"
    fi

    if [[ -z $ECCI_MONTTOR_SOURCE_PASSWORD ]];
    then
        export ECCI_MONTTOR_SOURCE_PASSWORD="anypasswd"
    fi

    if [[ -z $ECCI_MONITOR_FORWARD_IP ]];
    then
        echo "error: The IP of the forwarding mqtt needs to be provided"
        exit $1
    fi

    if [[ -z $ECCI_MONITOR_FORWARD_PORT ]];
    then
        echo "error: The port of the forwarding mqtt needs to be provided"
        exit $1
    fi

    if [[ -z $ECCI_MONITOR_FORWARD_USERNAME ]];
    then
        echo "error: The username of acl of the forwarding mqtt needs to be provided"
        exit $1
    fi

    if [[ -z $ECCI_MONITOR_FORWARD_PASSWORD ]];
    then
        echo "error: The password of acl of the forwarding mqtt needs to be provided"
        exit $1
    fi
fi

if [[ "$ECCI_MONITOR_MODE" == "system" ]];
then
    until nc -w 1 emqx 1883; do
    >&2 echo "Wait for source service to start"
    sleep 1
    done

    >&2 echo "api-server is up - wait emqx broker"

    until nc -w 1 api-server 8000; do
    >&2 echo "Wait for forward service to start"
    sleep 1
    done

    >&2 echo "service lanuch"
fi

exec $cmd