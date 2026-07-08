from fastapi import FastAPI, Request, Query
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from uuid import uuid4
from datetime import datetime, timezone
import time
import json


app = FastAPI()


# -------------------------
# Startup time
# -------------------------

START_TIME = time.time()


# -------------------------
# Prometheus counter
# -------------------------

REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests"
)


# -------------------------
# In-memory structured logs
# -------------------------

LOGS = []


def add_log(path, request_id, level="INFO"):

    entry = {
        "level": level,
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": path,
        "request_id": request_id
    }

    LOGS.append(entry)

    # keep only recent logs
    if len(LOGS) > 500:
        LOGS.pop(0)



# -------------------------
# Middleware
# -------------------------

@app.middleware("http")
async def logging_middleware(request: Request, call_next):

    request_id = str(uuid4())

    REQUEST_COUNTER.inc()

    response = await call_next(request)

    add_log(
        path=request.url.path,
        request_id=request_id
    )

    response.headers["X-Request-ID"] = request_id

    return response



# -------------------------
# Work endpoint
# -------------------------

@app.get("/work")
def work(n: int = Query(...)):

    done = 0

    for _ in range(n):
        done += 1


    return {
        "email": "25ds1000094@ds.study.iitm.ac.in",
        "done": done
    }



# -------------------------
# Prometheus metrics
# -------------------------

@app.get("/metrics")
def metrics():

    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )



# -------------------------
# Health check
# -------------------------

@app.get("/healthz")
def healthz():

    return {
        "status": "ok",
        "uptime_s": max(0, time.time() - START_TIME)
    }



# -------------------------
# Log tail
# -------------------------

@app.get("/logs/tail")
def logs_tail(limit: int = 10):

    return LOGS[-limit:]
