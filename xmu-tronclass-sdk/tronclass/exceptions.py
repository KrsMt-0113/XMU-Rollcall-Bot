"""Exceptions for xmu-tronclass-sdk."""


class TronClassError(Exception):
    """Base exception for all SDK errors."""
    def __init__(self, message: str, status_code: int = None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthError(TronClassError):
    """Login or session authentication failed."""


class NotFoundError(TronClassError):
    """Requested resource does not exist (404)."""


class PermissionError(TronClassError):
    """Insufficient permissions for the operation (403)."""


class RollcallError(TronClassError):
    """Error during rollcall answering."""


class RollcallExpiredError(RollcallError):
    """Rollcall has already expired."""


class RollcallAlreadyAnsweredError(RollcallError):
    """Rollcall was already answered."""


class PushError(TronClassError):
    """Error in the push notification subsystem."""
