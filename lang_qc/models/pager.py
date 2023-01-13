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

from pydantic import BaseModel, Field, PositiveInt

from lang_qc.models.qc_flow_status import QcFlowStatusEnum


class PagedResponse(BaseModel):
    """
    A response model for paged data.
    """

    page_size: PositiveInt = Field(
        title="Size of the page",
        description="""
        Size of the page, i.e. the number of objects that the client expects
        to receive.
        """,
    )
    page_number: PositiveInt = Field(
        title="Page sequential number",
        description="""
        The sequential number of the page that is requested by the client.
        The pages are numbered starting from one.
        """,
    )

    total_number_of_items: int = Field(
        default=0,
        title="Total number of unpaged objects",
        description="""
        Total number of unpaged objects. Needed by the UI in order to display
        correct buttons in the paging widget.
        """,
    )

    def slice_data(self, data: List) -> List:
        """
        A helper method to enable child classes to select pages in a uniform
        way.

        Given a list of items returns a slice of this list that corresponds
        to the page specified by this object's attributes. If the argument
        list is empty or shorter that expected, an empty list is returned.
        """
        from_number = self.page_size * (self.page_number - 1)
        to_number = from_number + self.page_size
        return data[from_number:to_number]


class PagedStatusResponse(PagedResponse):
    """
    A response model for paged data that relates to a particular QC flow
    status, described by the `qc_flow_status` attribute.
    """

    qc_flow_status: QcFlowStatusEnum = Field(
        title="QC flow status", description="QC flow status used for the selection."
    )
