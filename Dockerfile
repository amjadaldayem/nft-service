FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app
COPY ./requirements2.txt ./main ./ish /app/

RUN pip3 install --no-cache-dir -r /app/requirements2.txt
RUN yum install -y wget && wget https://github.com/remind101/ssm-env/releases/download/v0.0.3/ssm-env \
    && chmod +x /app/ssm-env && yum clean all

COPY ./app /app/app
COPY ./slab /app/slab

ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 80

ENTRYPOINT ["/app/ssm-env", "-with-decryption"]