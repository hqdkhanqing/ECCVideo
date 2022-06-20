FROM python:3.6.9-alpine3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /file-manager/

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add --update --no-cache bash

COPY docker/file-manager/requirements.txt .
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY docker/file-manager/file-manager-entrypoint.sh .
COPY edgeai/file-manager/src .

WORKDIR /file-manager/

# ENTRYPOINT ["./file-manager-entrypoint.sh"]

ENTRYPOINT ["python3","main.py"]