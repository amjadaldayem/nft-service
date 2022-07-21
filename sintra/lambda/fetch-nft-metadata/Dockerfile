FROM public.ecr.aws/x0l3b3a0/public-images:python3.8

COPY src ${LAMBDA_TASK_ROOT}/src

RUN python -m pip install --no-cache-dir -r src/requirements.txt

CMD ["src.app.lambda_handler"]