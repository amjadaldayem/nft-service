# Base Lambda Image
FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app
COPY requirements.txt ./main /app/

RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

ENV PYTHONPATH=/app:$PYTHONPATH
