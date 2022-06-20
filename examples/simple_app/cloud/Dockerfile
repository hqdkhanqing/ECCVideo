FROM python:3.8-alpine

ENV PYTHONUNBUFFERED 1

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add --update --no-cache bash
COPY examples/simple_app/cloud/requirements.txt /
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY examples/simple_app/cloud/main.py /
COPY examples/simple_app/cloud/ecci_sdk.py /

ENTRYPOINT ["python3","/main.py"]