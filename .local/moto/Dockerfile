FROM python:3.8.12-alpine

WORKDIR /usr/src/app

EXPOSE 5050

RUN apk add build-base libffi-dev
RUN pip install -U pip && pip install moto==2.3.0 flask Flask-Cors python-jose

CMD ["moto_server", "-p5050", "-H0.0.0.0"]