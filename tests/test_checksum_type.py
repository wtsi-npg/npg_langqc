import re

import pytest
from pydantic import BaseModel

from lang_qc.util.type_checksum import ChecksumSHA256


class ChecksumSHA256User(BaseModel):
    product_chcksm: ChecksumSHA256


def test_valid_checksum():
    id = "e47765a207c810c2c281d5847e18c3015f3753b18bd92e8a2bea1219ba3127ea"
    t = ChecksumSHA256User(product_chcksm=id)
    assert t.product_chcksm == id


def test_undefined_checksums():
    with pytest.raises(Exception, match=r"product_chcksm\s+Field required"):
        ChecksumSHA256User()


def test_numeric_checksums():
    id = int(64 * "2")
    with pytest.raises(Exception, match=r"String required"):
        ChecksumSHA256User(product_chcksm=id)


def test_invalid_length_checksums():
    for l in [20, 40]:
        id = l * "a2"
        with pytest.raises(
            Exception, match=r"product_chcksm\s+Value error, Invalid SHA256 checksum format"
        ):
            ChecksumSHA256User(product_chcksm=id)


def test_invalid_chars_checksums():
    id = 15 * "a1B2" + "34aq"
    with pytest.raises(
        Exception, match=r"product_chcksm\s+Value error, Invalid SHA256 checksum format"
    ):
        ChecksumSHA256User(product_chcksm=id)
