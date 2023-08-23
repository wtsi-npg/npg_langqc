"""
Custom run-time exceptions for LangQC.
"""


class InvalidDictValueError(Exception):
    """
    Custom exception for failures to validate input that should
    correspond to database dictionaries values such as, for example,
    and unknown QC type.
    """


class InconsistentInputError(Exception):
    """
    Custom exception for cases when individual values of attributes
    are valid, but are inconsistent or mutually exclusive in regards
    of the QC state that has to be assigned.
    """


class EmptyListOfRunNamesError(Exception):
    """Exception to be used when the list of run names is empty."""


class RunNotFoundError(Exception):
    """Exception to be used when no well metrics data for a run is found."""
