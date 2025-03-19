import json


class BaseRestException(Exception):
    message: str = "No msg"
    status: int = 400
    err_code: str = "400"

    def __init__(
        self, message: str | None = None, status: int | None = None, **kwargs
    ) -> None:
        self._message = message or self.message
        self._status = status or self.status
        self.details = kwargs or {}
        self.details.setdefault("message", self._message)
        self.details.setdefault("err_code", self.err_code)

        super().__init__(self._message, self._status, self.details)

    def __repr__(self) -> str:
        if self.details:
            return json.dumps(self.details)
        return super().__repr__()
