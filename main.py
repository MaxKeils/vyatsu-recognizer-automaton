from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from config import get_settings
from database.database import init_db
from fastapi.middleware.cors import CORSMiddleware

from routes import automaton_routes
from routes import configuration_routes, task_routes, user_routes, submission_routes
from routes import progress_routes, admin_routes

# Кастомная схема для ошибок валидации
validation_error_response = {
    422: {
        "description": "Ошибка валидации данных",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "example": False
                        },
                        "message": {
                            "type": "string",
                            "example": "Ошибка валидации данных"
                        },
                        "errors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": ["Поле 'section_number': ensure this value is less than or equal to 3"]
                        }
                    },
                    "required": ["success", "message", "errors"]
                }
            }
        }
    }
}

def create_application() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        docs_url="/docs",
        title="Vyatsu Recognizer Automaton API",
        version="2.1",
        description="API для системы проверки автоматов с посекционной проверкой",
        responses=validation_error_response
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Обработчик ошибок валидации
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
            message = error["msg"]
            errors.append(f"Поле '{field}': {message}" if field else message)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Ошибка валидации данных",
                "errors": errors
            }
        )

    # Обработчик HTTPException (наши бизнес-ошибки)
    from fastapi.exceptions import HTTPException as FastAPIHTTPException
    
    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail if isinstance(exc.detail, str) else "Ошибка",
                "errors": [exc.detail] if isinstance(exc.detail, str) else exc.detail
            }
        )

    # Обработчик общих исключений
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Логируем неожиданные ошибки
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Внутренняя ошибка сервера",
                "errors": [str(exc)]
            }
        )

    init_db()

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "database": "connected",
            "version": "2.1"
        }
    
    app.include_router(automaton_routes.router, prefix=settings.api_prefix)
    app.include_router(configuration_routes.router, prefix=settings.api_prefix)
    app.include_router(task_routes.router, prefix=settings.api_prefix)
    app.include_router(user_routes.router, prefix=settings.api_prefix)
    app.include_router(submission_routes.router, prefix=settings.api_prefix)
    app.include_router(progress_routes.router, prefix=settings.api_prefix)
    app.include_router(progress_routes.router_variants, prefix=settings.api_prefix)
    app.include_router(admin_routes.router, prefix=settings.api_prefix)

    return app

app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=get_settings().host,
        port=get_settings().port,
        reload=True
    )




