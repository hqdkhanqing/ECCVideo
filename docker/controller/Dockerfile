FROM python:3.6.9-alpine3.10
ENV PYTHONUNBUFFERED 1

WORKDIR /controller

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add  --update netcat-openbsd && rm -rf /var/cache/apk/*

COPY docker/controller/requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY docker/controller/wait-for-api-server-and-emqx.sh .

COPY edgeai/controller/src .

ENTRYPOINT ["./wait-for-api-server-and-emqx.sh"]

CMD ["python","main.py"]