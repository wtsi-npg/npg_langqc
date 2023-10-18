# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Authors:
#   Adam Blanchet
#   Marina Gourtovaia <mg8@sanger.ac.uk>
#   Kieron Taylor <kt19@sanger.ac.uk>
#
# This file is part of npg_langqc.
#
# npg_langqc is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic_settings import BaseSettings

from lang_qc.endpoints import config, pacbio_well, product


class Settings(BaseSettings):
    openapi_url: str = "/openapi/openapi.json"


settings = Settings()

logging.basicConfig(level=logging.INFO)

# Get origins from environment, must be a comma-separated list of origins
# for example, set CORS_ORIGINS=http://localhost:300,https://example.com:443
origins_env = os.environ.get("CORS_ORIGINS")
origins = []
if origins_env is not None:
    origins = origins_env.split(",")

app = FastAPI(title="LangQC", openapi_url=settings.openapi_url)
app.include_router(pacbio_well.router)
app.include_router(product.router)
app.include_router(config.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware)
