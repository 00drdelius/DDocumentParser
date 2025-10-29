from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles

from dd_parser import dd_parser_router


app = FastAPI(
    title="DDocumentParser",
    description="document parser for parsing various complex documents into knowledge base",
    version="1.0.0dev",
    docs_url=None,
    redoc_url=None
)
app.include_router(dd_parser_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins = "*",
    allow_methods = "*",
    allow_headers = "*",
)
app.mount("/statics",StaticFiles(directory="./statics"), "statics")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/statics/swagger-ui-bundle.js",
        swagger_css_url="/statics/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/statics/redoc.standalone.js",
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )