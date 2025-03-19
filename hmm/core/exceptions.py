import json
from typing import Any


class BaseRestException(Exception):
    message: str = "No msg"
    status: int = 400

    def __init__(self, *args, message: str | None = None, **kwargs) -> None:
        self._message = message or self.message
        if hasattr(kwargs, "status"):
            self.status = int(kwargs["status"])
        super().__init__(self._message, *args, **kwargs)


class BaseArgsRestException(BaseRestException):

    def __init__(
        self, *args, message: str | None = None, details: Any = None, **kwargs
    ) -> None:
        self.details = details or {}
        super().__init__(*args, message=message, **kwargs)
        match self.details:
            case dict():
                self.details.setdefault("message", self._message)
            case list():
                self.details = [self._message] + self.details

    def __repr__(self) -> str:
        if self.details:
            return json.dumps(self.details)
        return super().__repr__()


class UserNotFoundException(BaseArgsRestException):
    message = "User with this username not found"
    status = 400


class BadCredsError(BaseArgsRestException):
    message = "Bad creds"
    status = 400


class TokenSchemaError(BaseArgsRestException):
    message = "Invalid request"
    status = 400


class PasswordError(BaseArgsRestException):
    message = "Invalid password"
    status = 400


class NotASuperUserException(BaseArgsRestException):
    message = "User must be a super user"
    status = 403


class RegistrationError(BaseArgsRestException):
    message = "Registration error"
    status = 400
