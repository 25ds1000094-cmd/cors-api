from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4
import time
import jwt


app = FastAPI()


# -------------------------
# CORS CONFIGURATION
# -------------------------

ALLOWED_ORIGIN = "https://dash-7pz3pg.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# -------------------------
# REQUIRED RESPONSE HEADERS
# -------------------------

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start

        response.headers["X-Request-ID"] = str(uuid4())
        response.headers["X-Process-Time"] = f"{duration:.6f}"

        return response


app.add_middleware(MetricsMiddleware)


# -------------------------
# STATS ENDPOINT
# -------------------------

@app.get("/stats")
def stats(values: str = Query(...)):

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


# -------------------------
# JWT VERIFICATION CONFIG
# -------------------------

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


# -------------------------
# TOKEN VERIFICATION
# -------------------------

@app.post("/verify")
async def verify(data: dict):

    token = data.get("token")

    if not token:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

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
