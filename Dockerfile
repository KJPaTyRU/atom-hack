FROM python:3.10-slim AS python-base
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.6.0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false
ENV PATH="$POETRY_PATH/bin:$VENV_PATH/bin:$PATH"


FROM python-base AS poetry
WORKDIR /usr/src/app
RUN apt-get update \
    && apt-get install -y \
        # deps for installing poetry
        curl \
        python3-poetry \
        netcat-traditional \
        vim nano \
    && poetry --version \
    \
    # cleanup
    && rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-interaction --no-ansi -vvv --no-dev

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

COPY . ./

EXPOSE $SERVER_PORT

ENTRYPOINT ["./entrypoint.sh"]
