FROM emqx/emqx:v3.2.4

COPY docker/pubsub-broker/cloud/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
COPY docker/pubsub-broker/cloud/start.sh /usr/bin/start.sh

ENV EMQX_MQTT__MAX_PACKET_SIZE=5MB
# ENV EMQX_ACL_NOMATCH=deny

ENTRYPOINT ["sh","/usr/bin/docker-entrypoint.sh"]

CMD ["sh","/usr/bin/start.sh"]