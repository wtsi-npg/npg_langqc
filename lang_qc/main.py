# Copyright (c) 2022 Genome Research Ltd.
#
# Author: Adam Blanchet <ab59@sanger.ac.uk>
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

from fastapi import FastAPI
from starlette.responses import RedirectResponse

from lang_qc.endpoints.inbox import router as pacbio_run_router
from lang_qc.endpoints.pacbio_run import router as inbox_router

app = FastAPI(title="LangQC")
app.include_router(pacbio_run_router, prefix="/pacbio")
app.include_router(inbox_router, prefix="/pacbio")


@app.get("/")
async def root():
    """Redirect from root to docs."""
    return RedirectResponse(url="/docs")
