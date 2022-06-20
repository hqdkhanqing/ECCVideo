FROM emqx/emqx-edge:v3.2.4

COPY docker/pubsub-broker/edge/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
COPY docker/pubsub-broker/edge/start.sh /usr/bin/start.sh

ENV EMQX_BRIDGE__MQTT__EDGEAI__START_TYPE=auto

ENV EMQX_MQTT__MAX_PACKET_SIZE=5MB

ENTRYPOINT ["sh","/usr/bin/docker-entrypoint.sh"]

CMD ["sh","/usr/bin/start.sh"]