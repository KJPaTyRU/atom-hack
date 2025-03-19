import pydantic_core
from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from hmm.config import get_settings
from hmm.exceptions import BaseRestException

_ERROR_FUNC = get_settings().logging.logger_error_func


def default_catch_exception(app: FastAPI):

    @app.exception_handler(pydantic_core._pydantic_core.ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: pydantic_core._pydantic_core.ValidationError
    ):
        return Response(
            exc.json(),
            status_code=403,
            headers={"Content-Type": "application/json"},
        )

    @app.exception_handler(BaseRestException)
    async def arg_rest_exception_handler(
        request: Request, exc: BaseRestException
    ):
        _ERROR_FUNC(
            "{} | {} | {}", exc.__class__.__name__, exc.status, exc.details
        )
        return JSONResponse(
            jsonable_encoder(exc.details), status_code=exc.status
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        _ERROR_FUNC(
            "{} | {} | {}",
            exc.__class__.__name__,
            exc.status_code,
            dict(request.headers.items()),
        )
        return JSONResponse(
            content={"detail": exc.detail, "name": exc.__class__.__name__},
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def base_exception_handler(request: Request, exc: Exception):
        _ERROR_FUNC(exc)
        return JSONResponse(
            jsonable_encoder(
                dict(details=str(exc), class_name=exc.__class__.__name__)
            ),
            status_code=500,
        )
