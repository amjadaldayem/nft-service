FROM public.ecr.aws/python:3.8

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \ 
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.1.3

RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ${LAMBDA_TASK_ROOT}

RUN POETRY_VIRTUALENVS_CREATE=false \
    poetry install --no-dev --no-root --no-interaction --no-ansi

COPY data_api ${LAMBDA_TASK_ROOT}/data_api

CMD ["data_api.main.handler"]

