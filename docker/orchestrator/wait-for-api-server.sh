#!/bin/sh
# wait-for-api-server.sh

set -e
cmd="$@"

# if   [ -z $ECCI_WEBSOCKET_PORT ];
# then 
#     echo   "no ECCI_WEBSOCKET_PORT "
#     exit
# fi


until nc -w 1 api-server 8000; do
  >&2 echo "Wait for api-server to start"
  sleep 1
done

>&2 echo "api-server is up - service lanuch"

exec $cmd