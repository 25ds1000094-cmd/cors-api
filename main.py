from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4
import time
import jwt
import yaml
import os
from dotenv import load_dotenv


app = FastAPI()


# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# REQUIRED HEADERS
# -------------------------

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        response.headers["X-Request-ID"] = str(uuid4())
        response.headers["X-Process-Time"] = f"{time.perf_counter()-start:.6f}"

        return response


app.add_middleware(MetricsMiddleware)


# =====================================================
# QUESTION 1 - STATS
# =====================================================

@app.get("/stats")
def stats(values: str):

    numbers = [int(x.strip()) for x in values.split(",")]

    total = sum(numbers)

    return {
        "email": "25ds1000094@ds.study.iitm.ac.in",
        "count": len(numbers),
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / len(numbers)
    }


# =====================================================
# QUESTION 2 - JWT VERIFY
# =====================================================

ISSUER = "https://idp.exam.local"

AUDIENCE = "tds-dmw8zfd5.apps.exam.local"


PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----
"""


@app.post("/verify")
async def verify(data: dict):

    token = data.get("token")

    try:

        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }

    except Exception:

        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )


# =====================================================
# QUESTION 3 - CONFIG PRECEDENCE
# =====================================================


DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000"
}


YAML_CONFIG = {
    "port": 8522,
    "workers": 15,
    "debug": False,
    "log_level": "warning",
    "api_key": "key-zijl9ts246"
}


def str_to_bool(value):
    return str(value).lower() in [
        "true",
        "1",
        "yes",
        "on"
    ]


@app.get("/effective-config")
def effective_config(
    set: list[str] | None = Query(default=None)
):

    config = DEFAULTS.copy()

    # YAML layer
    config.update(YAML_CONFIG)


    # .env layer
    dotenv_values = {
        "workers": "9",
        "debug": "true",
        "log_level": "error"
    }

    config.update(dotenv_values)


    # OS environment layer
    os_values = {
        "port": "8768",
        "debug": "false"
    }

    config.update(os_values)


    # CLI overrides
    if set:

        for item in set:

            key, value = item.split("=", 1)
            config[key] = value


    # Type conversion

    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])
    config["debug"] = str_to_bool(config["debug"])

    config["log_level"] = str(config["log_level"])

    # Secret masking
    config["api_key"] = "****"


    return config
