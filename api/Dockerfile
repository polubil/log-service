FROM ubuntu:noble AS webapi

ARG python_version=3.14

EXPOSE 8000

SHELL ["/bin/sh", "-exc"]

RUN apt-get update && apt-get install -y curl

COPY --from=ghcr.io/astral-sh/uv:0.11.24 /uv /uvx /bin/

ENV UV_PYTHON=${python_version} \
    UV_PYTHON_DOWNLOADS=manual \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONOPTIMIZE=1

COPY pyproject.toml uv.lock VERSION /app/

WORKDIR /app

RUN uv python install ${python_version}

RUN uv sync --no-dev --locked --no-install-project

ENV UV_PYTHON=$UV_PROJECT_ENVIRONMENT

RUN sed -Ei "s/^(version = \")0\.0\.0(\")$/\1$(cat VERSION)\2/" pyproject.toml

RUN uv sync --no-dev --no-editable --frozen

COPY /src/ /app/src/
COPY main.py /app/

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
