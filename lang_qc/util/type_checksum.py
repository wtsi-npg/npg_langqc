import re

CHECKSUM_REGEX = re.compile("^[a-fA-F0-9]{64}$")


class ChecksumSHA256(str):
    """
    SHA256 checksum validation.

    It is possible to set validation on individual fields or
    URL components using, for example, the `constr` type. The creation
    of this custom type is justified by the fact that the validation
    of the product ID, which is a SHA256 checksum, is needed in
    multiple modules of this distribution.

    See https://docs.pydantic.dev/1.10/usage/types/#custom-data-types
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern=CHECKSUM_REGEX,
            examples=[
                "e47765a207c810c2c281d5847e18c3015f3753b18bd92e8a2bea1219ba3127ea"
            ],
        )

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("String required")
        m = CHECKSUM_REGEX.fullmatch(v)
        if not m:
            raise ValueError("Invalid SHA256 checksum format")
        return cls(v)

    def __repr__(self):
        return f"ChecksumSHA256({super().__repr__()})"
