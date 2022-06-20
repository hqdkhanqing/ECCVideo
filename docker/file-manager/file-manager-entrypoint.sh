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


if [[ -z "$ECCI_BROKER_IP" ]]; 
then
    echo "error: The IP of the subscribing mqtt needs to be provided"
    exit $1
fi

if [[ -z $ECCI_BROKER_PORT ]];
then
    echo "error: The PORT of the subscribing mqtt needs to be provided"
    exit $1
fi

if [[ -z $ECCI_MINIO_IP ]];
then
    echo "error: The IP of the minio server needs to be provided"
    exit $1
fi

if [[ -z $ECCI_MINIO_PORT ]];
then
    echo "error: The port of the minio server needs to be provided"
    exit $1
fi

if [[ -z $ECCI_MINIO_ACCESS_KEY ]];
then
    echo "error: The access key of acl of the minio server needs to be provided"
    exit $1
fi

if [[ -z $ECCI_MINIO_SECRET_KEY ]];
then
    echo "error: The secret key of acl of the minio server needs to be provided"
    exit $1
fi

until nc -w 1 minio 9000; do
>&2 echo "Wait for source service to start"
sleep 1
done

>&2 echo "service lanuch"

exec $cmd