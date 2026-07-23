from fastapi import FastAPI

from backend.routes.inspect import router as inspect_router

app = FastAPI()
app.include_router(inspect_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
