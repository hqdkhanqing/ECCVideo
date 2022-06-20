FROM python:3.6.9-alpine3.10
ENV PYTHONUNBUFFERED 1

WORKDIR /orchestrator

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add  --update netcat-openbsd && rm -rf /var/cache/apk/*

COPY docker/orchestrator/requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY docker/orchestrator/wait-for-api-server.sh .

COPY edgeai/orchestrator/src .

ENTRYPOINT ["./wait-for-api-server.sh"]

CMD ["python","main.py"]