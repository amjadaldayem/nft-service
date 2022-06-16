FROM python:3.8.12-slim

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \ 
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.1.3

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /sintra

COPY poetry.lock pyproject.toml /sintra/

RUN POETRY_VIRTUALENVS_CREATE=false \
    poetry install --no-dev --no-root --no-interaction --no-ansi

COPY data_api/ /sintra/data_api/

CMD ["uvicorn", "data_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

