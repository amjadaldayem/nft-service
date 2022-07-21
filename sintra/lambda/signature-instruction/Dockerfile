FROM public.ecr.aws/lambda/python:3.8

RUN yum install -y gcc

COPY src ${LAMBDA_TASK_ROOT}/src

RUN python -m pip install --no-cache-dir -r src/requirements.txt

# Use proper init
ADD https://sintra-shared-assets.s3.us-west-2.amazonaws.com/mi_linux_v0.6 /mi_linux
ADD https://sintra-shared-assets.s3.us-west-2.amazonaws.com/lambda-entrypoint.sh /lambda-entrypoint.sh
RUN chmod +x /mi_linux

CMD ["src.app.lambda_handler"]