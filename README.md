#  Long Read QC

## Install and run locally

You can install the package with `pip install .` from the repository's root.
Alternatively you can use [Poetry](https://python-poetry.org/docs/basic-usage/#installing-dependencies) to install and manage a virtual environment.

Then set two environment variables:

 - `DB_URL`: currently refers to the mlwh's url, in the format: `mysql+pymysql://user:pass@host:port/dbname`
 - `CORS_ORIGINS`: a comma-separated list of origins to allow CORS, e.g: `http://localhost:3000,https://example.com:443`

Finally, run the server: `uvicorn lang_qc.main:app`. 
Or `uvicorn lang_qc.main:app --reload` to reload the server on code changes.
