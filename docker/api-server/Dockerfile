FROM python:3.6.9-alpine3.10
ENV PYTHONUNBUFFERED 1

WORKDIR /api-server/

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add  --update gcc libc-dev linux-headers python3-dev postgresql-dev postgresql-client libffi-dev bash
COPY docker/api-server/requirements.txt .
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY edgeai/api-server/server .
COPY docker/api-server/wait-for-postgres.sh .

ENTRYPOINT ["./wait-for-postgres.sh"]

CMD ["python3","manage.py","runserver","0.0.0.0:8000"]