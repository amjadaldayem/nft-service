FROM public.ecr.aws/lambda/python:3.8

RUN yum install -y gcc

COPY src ${LAMBDA_TASK_ROOT}/src

RUN python -m pip install --no-cache-dir -r src/requirements.txt

CMD ["src.app.lambda_handler"]