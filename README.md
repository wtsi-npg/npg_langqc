#  Long Read QC

Please see the documents in the [docs](docs) folder for documentation on
subjects other than development, testing and deployment.

## Install and run locally

You can install the package with `pip install .` from the repository's root.
Alternatively you can use [Poetry](https://python-poetry.org/docs/basic-usage/#installing-dependencies)
to install and manage a virtual environment. Poetry will demand python => 3.10
available via package manager or pyenv.

Then set two environment variables:

- `DB_URL`: currently refers to the mlwh's url, in the format: `mysql+pymysql://user:pass@host:port/dbname`
- `CORS_ORIGINS`: a comma-separated list of origins to allow CORS, e.g: `http://localhost:3000,https://example.com:443`

Finally, run the server: `uvicorn lang_qc.main:app`.
Or `uvicorn lang_qc.main:app --reload` to reload the server on code changes.

## Using docker-compose

### Requirements

The deployment was tested with versions at least as recent as:

- `Docker version 20.10.5 and 20.10.8`
- `docker-compose version 1.28.6 and 1.29.2`

Think about using a more recent version of Ubuntu, for example `focal` rather than `bionic`.
The ports you would like to expose should also be open on your server.

To run the server, create an env file with the following template:

```bash
OIDCProviderMetadataURL=<identityproviderhostURL>/.well-known/openid-configuration # e.g. https://accounts.google.com/.well-known/openid-configuration
OIDCClientID=<yourclientID> # set by the OIDC Provider
OIDCClientSecret=<yourclientsecret> # set by the OIDC Provider
ODICCryptoPassphrase=somesecurepassphrase # you can choose this
OIDCRedirectURI=https://example.com/login-redirect # must match what is set on the OIDC Provider side
CORS_ORGINS=https://example.com:<someport> # most likely not needed anymore, probably can be left blank
QCDB_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>?charset=utf8mb4 # mlwh db
DB_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>?charset=utf8mb4 # qc db
CERT_FOLDER=/absolute/path/to/certs/folder # must contain `cert.pem` and `key.pem`
SERVER_HOST=https://example.com:443 # can omit port if standard, used for frontend build to refer to right API server.
HTTPS_PORT=443 # port on which the deployment will be exposed.
```

You might want to `chmod 600 /path/to/env/file` as it contains passwords.

Then from the root of this repository, run :
Build: `docker-compose --env-file /path/to/env/file build`
Run: `docker-compose --env-file /path/to/env/file up -d`

Finally, you can setup a systemd service in `/etc/systemd/system/npg_langqc.service` (change the paths accordingly):

```conf
[Unit]
Description=%i service with docker compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/path/to/repository/root
ExecStart=/usr/local/bin/docker-compose --env-file /path/to/env/file up -d --remove-orphans
ExecStop=/usr/local/bin/docker-compose --env-file /path/to/env/file  down

[Install]
WantedBy=multi-user.target
```

### Development setup

Follow the same steps as above. Then use `docker-compose.dev.yml` to override `docker-compose.yml`:

Build:

```sh
docker-compose \
  --env-file /path/to/env/file
  -f docker-compose.yml
  -f docker-compose.dev.yml
  build
```

Run:

```sh
docker-compose \
  --env-file /path/to/env/file
  -f docker-compose.yml
  -f docker-compose.dev.yml
  up -d
```

The `/lang_qc/` folder will be bind-mounted into the lang_qc docker container, and the server will hot-reload with
your changes. Additionally, two databases will be spun up with the default credentials used when running
`pytest` in the project (as of writing these will not have the schema setup by default: this is not a problem
for running unit tests, but if you want to use these databases to test the web app then you must create the schemas and
populate the databases with some data.).

Similarly, the `/frontend/{src,public}` folders will be bind-mounted into the longue_vue container, and the server will hot-reload
your changes. You will still need to reload your browser to see the changes.
Remember to change the url to the API in the JS code.
Any change that is done in any file not in `/frontend/{public,src}` will require a docker-compose build.

## Using Docker

This repository provides a [Docker image](https://github.com/wtsi-npg/npg_langqc/pkgs/container/npg_langqc).
The image is configured to use SSL for the server, running uvicorn.

The following instructions assume you have a recent Ubuntu system with Docker installed,
and your desired ports open.

### Step 1

Copy over SSL certificates, put them in a folder and name them `ca.pem`, `key.pem`
and`cert.pem` or create symlinks to them using these names.

### Step 2

Create a config folder containing one file, `uvicorn_env`, with the following contents:

```sh
DB_URL=<insert your DB URL here>
CORS_ORIGINS=<comma-separated list of origins for which to allow CORS>
```

An example is:

```sh
DB_URL=mysql+pymysql://myuser:mypass@example.com:3306/mydbname
CORS_ORIGINS=http://localhost:3000,https://example.com:443
```

### Step 3

Create an envfile containng the following:

```bash
export CERT_FOLDER=/path/to/cert/folder
export CONFIG_FOLDER=/path/to/config/folder
export SSL_PORT=<your desired port for the server> # e.g. SSL_PORT=443
```

Source this file: `. envfile`

### Step 4

Run the server (replace `devel` with `latest` if you wish to run the `master` branch
instead.):

```bash
docker run \
  --name npg_langqc \
  -p ${SSL_PORT}:443 \
  -v ${CERT_FOLDER}:/certs \
  -v ${CONFIG_FOLDER}:/config \
  ghcr.io/wtsi-npg/npg_langqc:devel
```

---------------------------------------------------------------------------------------------------

The next steps are to set the server up as a SystemD service.

### Step 5

Create a service file `/etc/systemd/system/npg_langqc.service`, with the following
contents:

```conf
[Unit]
Description=npg_langqc Docker container
Wants=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a npg_langqc
ExecStop=/usr/bin/docker stop -t 10 npg_langqc

[Install]
WantedBy=multi-user.target
```

### Step 6

Enable and start the service:

```bash
sudo systemctl enable npg_langqc.service
sudo systemctl start npg_langqc.service
```

### Step 7

Verify everything is working:

```bash
systemctl status npg_langqc.service
journalctl -xe
```
