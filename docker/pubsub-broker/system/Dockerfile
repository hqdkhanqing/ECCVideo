FROM emqx/emqx:v3.2.4

COPY docker/pubsub-broker/system/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
COPY docker/pubsub-broker/system/start.sh /usr/bin/start.sh

ENV EMQX_ALLOW_ANONYMOUS=false

ENV EMQX_ACL_NOMATCH=deny

ENV EMQX_MQTT__MAX_PACKET_SIZE=5MB

ENTRYPOINT ["sh","/usr/bin/docker-entrypoint.sh"]

CMD ["sh","/usr/bin/start.sh"]