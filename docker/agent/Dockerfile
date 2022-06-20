FROM python:3.6.9-alpine3.10
ENV PYTHONUNBUFFERED 1

WORKDIR /agent

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add --update gcc libc-dev linux-headers bash docker-cli docker-compose && rm -rf /var/cache/apk/*

COPY docker/agent/requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

ENV ECCI_DOCKER_COMPOSE_YML_PATH ./data/apps/

COPY edgeai/agent/src/ /agent/

COPY docker/agent/docker-entrypoint.sh .

ENTRYPOINT ["./docker-entrypoint.sh"]

CMD ["python","main.py"]