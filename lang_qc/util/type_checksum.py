import re

from pydantic_core import core_schema

CHECKSUM_REGEX = re.compile("^[a-fA-F0-9]{64}$")


class ChecksumSHA256(str):
    """
    SHA256 checksum validation.

    It is possible to set validation on individual fields or
    URL components using, for example, the `constr` type. The creation
    of this custom type is justified by the fact that the validation
    of the product ID, which is a SHA256 checksum, is needed in
    multiple modules of this distribution.

    Cribbed from https://github.com/pydantic/pydantic-extra-types/blob/main/pydantic_extra_types/mac_address.py # noqa: E501
    due to opaque handling of fundamental types in Pydantic docs
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.with_info_before_validator_function(
            cls.validate, core_schema.str_schema()
        )

    @classmethod
    def _validate(cls, __input_value, _):
        return cls.validate(__input_value.encode())

    @classmethod
    def validate(cls, v, _):
        if not isinstance(v, str):
            raise TypeError("String required")
        m = CHECKSUM_REGEX.fullmatch(v)
        if not m:
            raise ValueError("Invalid SHA256 checksum format")
        return v

    def __repr__(self):
        return f"ChecksumSHA256({super().__repr__()})"


class PacBioWellSHA256(ChecksumSHA256):
    """
    A checksum generated from the coordinates of a single well on a plate in a PacBio run
    """

    pass


class PacBioProductSHA256(ChecksumSHA256):
    """
    A checksum generated from the combination of run, well, plate and any tags required for
    deplexing, see `npg_id_generation.pac_bio.PacBioEntity`.
    Tags only contribute to the checksum when samples are multiplexed.
    """

    pass
