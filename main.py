from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

app = FastAPI()

ALLOWED_ORIGIN = "https://dash-7pz3pg.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_headers(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    elapsed = time.time() - start

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"

    return response


@app.get("/stats")
def stats(
    request: Request,
    values: str = Query(...)
):
    numbers = [int(x.strip()) for x in values.split(",") if x.strip()]

    if not numbers:
        return JSONResponse(
            status_code=400,
            content={"error": "No values provided"}
        )

    total = sum(numbers)
    count = len(numbers)

    return {
        "email": "26t2_cs2008-announce@study.iitm.ac.in",
        "count": count,
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": round(total / count, 6)
    }
