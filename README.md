# Module 10 Secure User API

## Overview

This project extends the FastAPI calculator application with a secure
SQLAlchemy user model, Pydantic validation, password hashing, PostgreSQL
integration tests, Docker deployment, image scanning, and an automated
GitHub Actions CI/CD pipeline.

## Features

- FastAPI calculator routes
- Secure user registration
- Unique usernames and email addresses
- Bcrypt password hashing
- Pydantic email and password validation
- PostgreSQL database storage
- Unit and integration testing
- Docker Compose deployment
- GitHub Actions testing and deployment
- Trivy container security scanning
- Docker Hub image publishing

## Project Structure

```text
app/
├── models/
├── schemas/
├── crud.py
├── database.py
├── operations/
└── security.py

tests/
├── unit/
├── integration/
└── e2e/