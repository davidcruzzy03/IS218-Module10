# main.py

import logging

import uvicorn
from fastapi import (Depends, FastAPI, HTTPException, Request, status)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.database import Base, engine, get_db
from app.models.user import User
from app.operations import add, divide, multiply, subtract
from app.schemas.user import UserCreate, UserRead

# ---------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Database table creation
# ---------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------
app = FastAPI(
    title="Module 10 Secure User and Calculator API",
    description=(
        "A FastAPI application containing calculator routes "
        "and secure user registration."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------
# Template configuration
# ---------------------------------------------------------

templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------
# Calculator Pydantic schemas
# ---------------------------------------------------------

class OperationRequest(BaseModel):
    """Request body for calculator operations."""

    a: float = Field(
        ...,
        description="The first number",
    )

    b: float = Field(
        ...,
        description="The second number",
    )

    @field_validator("a", "b")
    @classmethod
    def validate_numbers(cls, value: float) -> float:
        """Confirm that both submitted values are numeric."""

        if not isinstance(value, (int, float)):
            raise ValueError(
                "Both a and b must be numbers."
            )

        return value

class OperationResponse(BaseModel):
    """Successful calculator response."""

    result: float = Field(
        ...,
        description="The result of the operation",
    )

class ErrorResponse(BaseModel):
    """API error response."""

    error: str = Field(
        ...,
        description="Error message",
    )

# ---------------------------------------------------------
# Custom exception handlers
# ---------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Return HTTP errors using the project's error format."""

    logger.error(
        "HTTPException on %s: %s",
        request.url.path,
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return Pydantic validation errors using a readable format."""

    error_messages = "; ".join(
        [
            f"{error['loc'][-1]}: {error['msg']}"
            for error in exc.errors()
        ]
    )

    logger.error(
        "ValidationError on %s: %s",
        request.url.path,
        error_messages,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": error_messages},
    )

# ---------------------------------------------------------
# General routes
# ---------------------------------------------------------
@app.get("/health")
def health_check() -> dict[str, str]:
    """Allow Docker and GitHub Actions to check the application."""

    return {"status": "healthy"}

@app.get("/")
async def read_root(request: Request):
    """Serve the calculator HTML page."""

    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )

# ---------------------------------------------------------
# User routes
# ---------------------------------------------------------

@app.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def register_user(
    user_data: UserCreate,
    database: Session = Depends(get_db),
) -> User:
    """
    Create a new user.

    The submitted plain-text password is hashed before storage.
    The API response does not expose the password or password hash.
    """

    existing_username = crud.get_user_by_username(
        database,
        user_data.username,
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    existing_email = crud.get_user_by_email(
        database,
        str(user_data.email),
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    try:
        user = crud.create_user(
            database,
            user_data,
        )

        logger.info(
            "Created user with username: %s",
            user.username,
        )

        return user

    except IntegrityError as error:
        database.rollback()

        logger.error(
            "Database uniqueness error while creating user: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        ) from error

# ---------------------------------------------------------
# Calculator routes
# ---------------------------------------------------------
@app.post(
    "/add",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
)
async def add_route(
    operation: OperationRequest,
) -> OperationResponse:
    """Add two numbers."""

    try:
        result = add(
            operation.a,
            operation.b,
        )

        return OperationResponse(result=result)

    except Exception as error:
        logger.error(
            "Add Operation Error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@app.post(
    "/subtract",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
)
async def subtract_route(
    operation: OperationRequest,
) -> OperationResponse:
    """Subtract two numbers."""

    try:
        result = subtract(
            operation.a,
            operation.b,
        )

        return OperationResponse(result=result)

    except Exception as error:
        logger.error(
            "Subtract Operation Error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

@app.post(
    "/multiply",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
)
async def multiply_route(
    operation: OperationRequest,
) -> OperationResponse:
    """Multiply two numbers."""

    try:
        result = multiply(
            operation.a,
            operation.b,
        )

        return OperationResponse(result=result)

    except Exception as error:
        logger.error(
            "Multiply Operation Error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

@app.post(
    "/divide",
    response_model=OperationResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def divide_route(
    operation: OperationRequest,
) -> OperationResponse:
    """Divide two numbers."""

    try:
        result = divide(
            operation.a,
            operation.b,
        )

        return OperationResponse(result=result)

    except ValueError as error:
        logger.error(
            "Divide Operation Error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.error(
            "Divide Operation Internal Error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from error

# ---------------------------------------------------------
# Development server
# ---------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )