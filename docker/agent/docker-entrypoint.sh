#!/bin/sh

## Shell setting
if [[ ! -z "$DEBUG" ]]; then
    set -ex
else
    set -e
fi

for VAR in $(env)
do
    if [[ ! -z "$(echo $VAR | grep -E '^ECCI_')" ]]; then
        echo "$VAR"
    fi
done

if [[ -n "$ECCI_REGISTRY_URL" ]] && [[ -n "$ECCI_REGISTRY_USERNAME" ]] && [[ -n "$ECCI_REGISTRY_PASSWORD" ]]; then
    docker login -u $ECCI_REGISTRY_USERNAME -p $ECCI_REGISTRY_PASSWORD $ECCI_REGISTRY_URL
fi

exec "$@"