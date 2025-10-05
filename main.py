from fastapi import FastAPI, Depends
from config import get_settings

def create_application(
    settings = Depends(get_settings)
) -> FastAPI:
    app = FastAPI(
        docs_url="/docs"
    )

    @app.get("/health")
    async def health_check():
        """Endpoint проверки работоспособности."""
        return {"status": "healthy"}
    
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




