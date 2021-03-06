#  Long Read QC

## Install and run locally

You can install the package with `pip install .` from the repository's root.
Alternatively you can use [Poetry](https://python-poetry.org/docs/basic-usage/#installing-dependencies)
to install and manage a virtual environment.

Then set two environment variables:

- `DB_URL`: currently refers to the mlwh's url, in the format: `mysql+pymysql://user:pass@host:port/dbname`
- `CORS_ORIGINS`: a comma-separated list of origins to allow CORS, e.g: `http://localhost:3000,https://example.com:443`

Finally, run the server: `uvicorn lang_qc.main:app`.
Or `uvicorn lang_qc.main:app --reload` to reload the server on code changes.

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

```
DB_URL=<insert your DB URL here>
CORS_ORIGINS=<comma-separated list of origins for which to allow CORS>
```

An example is:

```
DB_URL=mysql+pymysql://myuser:mypass@example.com:3306/mydbname
CORS_ORIGINS=http://localhost:3000,https://example.com:443
```

### Step 3

Create an envfile containng the following:

```
export CERT_FOLDER=/path/to/cert/folder
export CONFIG_FOLDER=/path/to/config/folder
export SSL_PORT=<your desired port for the server> # e.g. SSL_PORT=443
```

Source this file: `. envfile`

### Step 4

Run the server (replace `devel` with `latest` if you wish to run the `master` branch
instead.):

```
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

```
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

```
sudo systemctl enable npg_langqc.service
sudo systemctl start npg_langqc.service
```

### Step 7

Verify everything is working:

```
systemctl status npg_langqc.service
journalctl -xe
```
