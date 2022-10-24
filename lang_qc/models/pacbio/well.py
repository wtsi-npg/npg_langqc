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

from datetime import datetime

from pydantic import BaseModel, Extra, Field

from lang_qc.models.qc_state import QcState
from lang_qc.models.pager import PagedResponse
from lang_qc.models.qc_flow_status import QcFlowStatusEnum

class PacBioWell(BaseModel, extra=Extra.forbid):
    """
    A response model for a single PacBio well on a particular PacBio run.
    The class contains the attributes that uniquely define this well (`run_name`
    and `level`), along with the time line and current QC state of this well.

    This model does not contain any information about data that was
    sequenced or QC metrics or assessment for such data.
    """

    label: str = Field(title="Well label", description="The label of the PacBio well")
    run_name: str = Field(
        title="Run name", description="PacBio run name as registered in LIMS"
    )
    run_start_time: datetime = Field(default=None, title="Run start time")
    run_complete_time: datetime = Field(default=None, title="Run complete time")
    well_start_time: datetime = Field(default=None, title="Well start time")
    well_complete_time: datetime = Field(default=None, title="Well complete time")
    qc_state: QcState = Field(
        default=None,
        title="Current QC state of this well",
        description="""
        Current QC state of this well as a QcState pydantic model.
        The well might have no QC state assigned. Whether the QC state is
        available depends on the lifecycle stage of this well.
        """,
    )


class PacBioPagedWells(PagedResponse, extra=Extra.forbid):
    """
    A response model for paged data about PacBio wells.
    """

    wells: List[PacBioWell] = Field (
        default=[],
        title="A list of PacBioWell objects",
        description="""
        A list of `PacBioWell` objects that corresponds to the QC flow status
        given by the `qc_flow_status` attribute and the page number and size
        specified secified by teh `page_size` and `page_number` attributes.
        """
    )
    qc_flow_status: QcFlowStatusEnum = Field(
        title="QC flow status",
        description="QC flow status used to filter select wells."
    )

