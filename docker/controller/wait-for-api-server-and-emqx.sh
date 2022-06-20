#!/bin/sh
# wait-for-api-server-and-emqx.sh

set -e
cmd="$@"

# if   [ -z $ECCI_CONTROLLER_WS_PORT ];
# then 
#     echo   "no ECCI_WEBSOCKET_PORT "
#     exit
# fi

# if   [ -z $ECCI_CONTROLLER_MQ_PORT ];
# then 
#     echo   "no ECCI_CONTROLLER_MQ_PORT "
#     exit
# fi

# ECCI_CONTROLLER_WS_PORT=$ECCI_CONTROLLER_WS_PORT
# ECCI_CONTROLLER_MQ_PORT=$ECCI_CONTROLLER_MQ_PORT

until nc -w 1 api-server 8000; do
  >&2 echo "Wait for api-server to start"
  sleep 1
done

>&2 echo "api-server is up - wait emqx broker"

until nc -w 1 emqx 1883; do
  >&2 echo "Wait for emqx broker to start"
  sleep 1
done

>&2 echo "emqx broker is up - service lanuch"

exec $cmd