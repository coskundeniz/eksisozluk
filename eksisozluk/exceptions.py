class EksiReaderException(Exception):
    """Base exception for eksisozluk reader"""


class EksiReaderPageRequestError(EksiReaderException):
    """Page request exception"""


class EksiReaderInvalidInputError(EksiReaderException):
    """Unexpected input exception"""


class EksiReaderMissingInputError(EksiReaderException):
    """Missing input exception"""


class EksiReaderNoChannelError(EksiReaderException):
    """Channel search exception"""


class EksiReaderDatabaseError(EksiReaderException):
    """Database operation exception"""
