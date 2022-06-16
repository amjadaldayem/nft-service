FROM public.ecr.aws/lambda/python:3.8

COPY src ${LAMBDA_TASK_ROOT}/src

RUN python -m pip install --no-cache-dir -r src/requirements.txt --target ${LAMBDA_TASK_ROOT}

CMD ["src.app.lambda_handler"]