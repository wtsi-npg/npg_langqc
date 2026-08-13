FROM python:3.12-slim as base

RUN apt-get update -qq \
    && apt-get install -qq --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r apprunner \
    && useradd -r -g apprunner apprunner

WORKDIR /code

# git and .git are needed only so setuptools-git-versioning can derive the
# version while building the project during the install below.
COPY ./pyproject.toml ./COPYING ./
COPY ./lang_qc ./lang_qc
COPY ./.git ./.git

# Install the dependencies; the app is run from the source tree (COPYed for
# production, bind-mounted for development), so the source and build inputs are
# removed once the install is done.
RUN pip install --no-cache-dir . \
    && rm -rf ./lang_qc ./.git ./pyproject.toml ./COPYING \
    && apt-get purge --auto-remove -qq -y git \
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
