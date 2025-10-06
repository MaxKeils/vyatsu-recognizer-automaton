from fastapi import FastAPI
from config import get_settings
from database.database import init_db

from routes import automaton_routes
from routes import configuration_routes, task_routes, user_routes, submission_routes

def create_application() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        docs_url="/docs",
    )

    # Initialize database
    init_db()

    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    # Include routers
    app.include_router(automaton_routes.router, prefix=settings.api_prefix)
    app.include_router(configuration_routes.router, prefix=settings.api_prefix)
    app.include_router(task_routes.router, prefix=settings.api_prefix)
    app.include_router(user_routes.router, prefix=settings.api_prefix)
    app.include_router(submission_routes.router, prefix=settings.api_prefix)

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




