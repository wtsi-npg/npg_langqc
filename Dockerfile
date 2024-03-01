FROM python:3.10 as requirements-stage

WORKDIR /tmp

RUN pip install --no-cache-dir poetry==1.1.13

COPY ./pyproject.toml ./poetry.lock /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.13.0a3-slim as base

RUN apt-get update -qq \
    && apt-get install -qq --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r apprunner \
    && useradd -r -g apprunner apprunner

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt \
    && apt-get remove -qq --autoremove git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

FROM base as production

COPY ./lang_qc /code/lang_qc
USER apprunner
WORKDIR /code
CMD ["uvicorn", "lang_qc.main:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "/certs/key.pem", "--ssl-certfile", "/certs/cert.pem", "--ssl-ca-certs", "/certs/ca.pem", "--env-file", "/config/uvicorn_env"]

FROM base as development
WORKDIR /code
USER apprunner
CMD ["uvicorn", "lang_qc.main:app" , "--reload"]
