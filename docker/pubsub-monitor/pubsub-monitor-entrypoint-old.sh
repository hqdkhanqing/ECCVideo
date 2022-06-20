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


if [ "$ECCI_MONITOR_MODE" == "system" ];
then
fi

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

exec $cmd