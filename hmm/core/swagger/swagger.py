import json
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, FastAPI

from fastapi.encoders import jsonable_encoder
from fastapi.openapi.docs import (
    swagger_ui_default_parameters,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import FileResponse, HTMLResponse


def _custom_get_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",  # noqa
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",  # noqa
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    oauth2_redirect_url: Optional[str] = None,
    init_oauth: Optional[Dict[str, Any]] = None,
    swagger_ui_parameters: Optional[Dict[str, Any]] = None,
) -> HTMLResponse:
    current_swagger_ui_parameters = swagger_ui_default_parameters.copy()
    if swagger_ui_parameters:
        current_swagger_ui_parameters.update(swagger_ui_parameters)

    js_btn = """
    <script>
    function copy(that){
    var inp =document.createElement('input');
    document.body.appendChild(inp)
    inp.value =that.textContent
    inp.select();
    document.execCommand('copy',false);
    inp.remove();
    }</script>
    """

    style_btn = """
    <style>

.uuid_btn {
  appearance: none;
  backface-visibility: hidden;
  background-color: #27ae60;
  border-radius: 8px;
  border-style: none;
  box-shadow: rgba(39, 174, 96, .15) 0 4px 9px;
  box-sizing: border-box;
  color: #fff;
  cursor: pointer;
  display: inline-block;
  font-family: Inter,-apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: normal;
  line-height: 1.5;
  outline: none;
  overflow: hidden;
  padding: 2px 5px;
  position: relative;
  text-align: center;
  text-decoration: none;
  transform: translate3d(0, 0, 0);
  transition: all .3s;
  user-select: none;
  -webkit-user-select: none;
  touch-action: manipulation;
  vertical-align: top;
  white-space: nowrap;
}

.uuid_btn:hover {
  background-color: #1e8449;
  opacity: 1;
  transform: translateY(0);
  transition-duration: .35s;
}

.uuid_btn:active {
  transform: translateY(2px);
  transition-duration: .35s;
}

.uuid_btn:hover {
  box-shadow: rgba(39, 174, 96, .2) 0 6px 12px;
}
    </style>"""  # noqa

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    </head>
    <body>
    {style_btn}
    <code onclick="copy(this)" class="uuid_btn" id="top-defaul-uuid"
    style="position: sticky;top:0%;
    left:50%">3fa85f64-5717-4562-b3fc-2c963f66afa6</code>
    <div id="swagger-ui">
    </div>
    {js_btn}
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>"""
    html += "const ui = SwaggerUIBundle({"
    html += f"url: '{openapi_url}',"

    for key, value in current_swagger_ui_parameters.items():
        html += f"{json.dumps(key)}: {json.dumps(jsonable_encoder(value))},\n"

    if oauth2_redirect_url:
        html += (
            "oauth2RedirectUrl: window.location.origin +"
            f" '{oauth2_redirect_url}',"
        )

    html += """
    presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
    })"""

    if init_oauth:
        html += f"""
        ui.initOAuth({json.dumps(jsonable_encoder(init_oauth))})
        """

    html += """
    </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


def init_swagger_routes(app: FastAPI, prefix="/api/py/secret-cdn"):

    route = APIRouter(prefix=prefix, include_in_schema=False)

    @route.get("/swagger.js")
    def get_js():
        path = Path(__file__).parent / "swagger-ui-bundle.js"
        return FileResponse(path)

    @route.get("/swagger.css")
    def get_css():
        path = Path(__file__).parent / "swagger-ui.css"
        return FileResponse(path)

    app.include_router(route)


def add_custom_swagger(
    app: FastAPI,
    prefix="/api/py/secret-cdn",
    swagger_ui_parameters: dict | None = None,
    docs_prefix: str | None = None,
    root_path: str | None = None,
    cdn_prefix: str | None = None,
):
    base_path = ""
    if docs_prefix:
        base_path = docs_prefix
    real_root_path = root_path if root_path else app.root_path
    _cdn_prefix = cdn_prefix if cdn_prefix else (real_root_path + prefix)

    @app.get(base_path + "/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return _custom_get_swagger_ui_html(
            # openapi_url=(
            #     app.openapi_url
            #     if openapi_url is None
            #     else openapi_url + "/openapi.json"
            # ),
            openapi_url=real_root_path + base_path + "/openapi.json",
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url=f"{_cdn_prefix}/swagger.js",
            swagger_css_url=f"{_cdn_prefix}/swagger.css",
            swagger_ui_parameters=swagger_ui_parameters,
        )

    @app.get(base_path + "/openapi.json", include_in_schema=False)
    async def custom_swagger_openapi() -> dict[str, Any]:
        return app.openapi()

    @app.get(
        real_root_path + (app.swagger_ui_oauth2_redirect_url or ""),
        include_in_schema=False,
    )
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    return app
