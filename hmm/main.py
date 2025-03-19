from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from hmm.core.middleware import default_catch_exception
from hmm.router import router
from hmm.config import get_settings
from hmm.core.swagger.swagger import add_custom_swagger, init_swagger_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("[Server] Inited")
    yield
    logger.info("[Server] Stopped")


def create_app():
    main_app = FastAPI(
        title="hmm server",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )

    if not get_settings().api.docs_disable:
        init_swagger_routes(main_app, prefix=get_settings().api.cdn_prefix)

        add_custom_swagger(
            main_app,
            prefix=get_settings().api.cdn_prefix,
            swagger_ui_parameters={"docExpansion": "none"},
            docs_prefix=get_settings().api.cdn_prefix,
        )

    # * Routes * #
    main_app.include_router(router)
    default_catch_exception(main_app)
    return main_app
