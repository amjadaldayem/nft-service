FROM 391319738221.dkr.ecr.us-west-2.amazonaws.com/public-images:python-3.8

COPY src ${LAMBDA_TASK_ROOT}/src

RUN python -m pip install --no-cache-dir -r src/requirements.txt

CMD ["src.app.lambda_handler"]