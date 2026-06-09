import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import user_router, health_router, auth_router
from app.core.logger import setup_logging

from app.core.exceptions import (
    IncorrectCredentialsException,
    UserNotFoundException,
    EmailAlreadyTakenException,
    DatabaseException,
)

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    finally:
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {status_code} - "
            f"{process_time:.4f}s"
        )
    return response


@app.exception_handler(IncorrectCredentialsException)
async def incorrect_credentials_handler(
    request: Request, exc: IncorrectCredentialsException
):
    return JSONResponse(
        status_code=401,
        content={"detail": "Incorrect email or password"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "User not found"},
    )


@app.exception_handler(EmailAlreadyTakenException)
async def email_taken_handler(request: Request, exc: EmailAlreadyTakenException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Email already registered"},
    )


@app.exception_handler(DatabaseException)
async def database_error_handler(request: Request, exc: DatabaseException):
    logger.error("Database operation failed")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred."},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please check the logs."},
    )


app.include_router(health_router)
app.include_router(user_router)
app.include_router(auth_router)
