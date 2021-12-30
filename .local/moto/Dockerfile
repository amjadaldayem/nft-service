FROM python:3.8.12-alpine

WORKDIR /usr/src/app

EXPOSE 5001

RUN apk add build-base libffi-dev
RUN pip install -U pip && pip install moto==2.3.0 flask Flask-Cors

CMD ["moto_server", "-p5001"]