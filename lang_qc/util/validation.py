# Copyright (c) 2023 Genome Research Ltd.
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

from typing import Annotated, List

from pydantic import Field, validate_arguments

"""
A collection of functions for validating inputs for cases
when a full pydantic class definition feels unnecessary.
"""

CHECKSUM_RE = "^[a-fA-F0-9]{64}$"


@validate_arguments
def check_product_id_is_valid(id_product: Annotated[str, Field(regex=CHECKSUM_RE)]):
    """
    Validation for a product ID string.
    Product ID is a SHA256 checksum, therefore, the product ID
    must be hexadecimal of length 64.

    Returns the argument id_product.
    """
    return id_product


@validate_arguments
def check_product_id_list_is_valid(
    id_products: Annotated[List[str], Field(min_items=1)]
):
    """
    Validation for a list of product IDs.
    The argument list should have at least one product ID.
    An error is raised on the first string that fails validation
    for a product ID.

    Returns the argument list.
    """
    return [check_product_id_is_valid(id) for id in id_products]
