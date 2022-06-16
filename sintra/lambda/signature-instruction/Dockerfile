FROM public.ecr.aws/lambda/python:3.8

COPY src/ ${LAMBDA_TASK_ROOT}

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD ["app.lambda_handler"]