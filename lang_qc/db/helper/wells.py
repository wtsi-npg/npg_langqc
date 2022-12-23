# Copyright (c) 2022 Genome Research Ltd.
#
# Author: Marina Gourtovaia <mg8@sanger.ac.uk>
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

from typing import List

from pydantic import Extra

from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWell
from lang_qc.models.pager import PagedStatusResponse


class PacBioPagedWellsFactory(PagedStatusResponse, extra=Extra.forbid):
    """
    Factory class to create `PacBioPagedWells` objects that correspond to
    the criteria given by the attributes of the object, i.e. `page_size`
    `page_number` and `qc_flow_status` attributes.
    """

    def wells2paged_wells(self, wells: List[PacBioWell]) -> PacBioPagedWells:
        """
        Given a list of `PacBioWell` objects, slices the list according to the
        value of the `page_size` and `page_number` attributes and returns a
        corresponding `PacBioPagedWells` object.
        """
        return PacBioPagedWells(
            page_number=self.page_number,
            page_size=self.page_size,
            total_number_of_items=len(wells),
            qc_flow_status=self.qc_flow_status,
            wells=self.slice_data(wells),
        )
