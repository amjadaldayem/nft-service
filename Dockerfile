FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app
COPY requirements.txt ./main /app/

RUN pip3 install --no-cache-dir -r /app/requirements.txt
RUN yum install -y wget && wget https://github.com/remind101/ssm-env/releases/download/v0.0.3/ssm-env \
    && chmod +x /app/ssm-env && yum clean all
COPY app /app/app

ENV PYTHONPATH=/app:$PYTHONPATH
ENTRYPOINT ["/app/ssm-env", "-with-decryption"]