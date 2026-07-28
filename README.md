# DataSkill-API
*A robust FastAPI backend application developed as part of a Software Engineering Internship.*

## About
DataSkill-API is a comprehensive SaaS-style backend service designed for corporate training and employee assessment. It provides a complete ecosystem for organizations to manage members, assign roles (Owner, Admin, User), and conduct regular assessments through a dynamic quiz system. The API handles complex workflows, including role-based access control (RBAC), temporary data caching, automated daily reminders, and detailed performance analytics.

## Key Features
* **Multi-Tenant Architecture:** Users can create and manage multiple companies, complete with an invite/request system and role-based permissions.
* **Universal Authentication:** Secure authentication supporting both traditional JWT (Login/Password) and Auth0 integration.
* **Dynamic Quiz Engine:** Creation of complex quizzes with multiple question types, participation limits, and scheduled daily completion tracking.
* **High-Performance Caching:** Utilizes Redis for temporary storage (48 hours) of user quiz responses before persistent database commits.
* **Advanced Analytics & Reporting:** Calculates user ratings and company-wide performance metrics, with options to export data to JSON and CSV formats.
* **Data Import:** Functionality to seamlessly parse and import new quizzes directly from Excel files.
* **Automated Workflows:** Scheduled background scripts to monitor quiz deadlines and trigger system notifications.
* **Cloud-Ready Deployment:** Fully containerized architecture with automated CI/CD pipelines deploying directly to AWS via GitHub Actions.

## Tech Stack
* **Core:** Python, FastAPI, Uvicorn
* **Databases:** PostgreSQL (asyncpg), Redis (redis.asyncio)
* **ORM & Migrations:** SQLAlchemy (AsyncSession), Alembic
* **Authentication:** JWT, Auth0
* **Testing:** pytest
* **DevOps & Infrastructure:** Docker, Docker Compose, GitHub Actions, AWS
* **Package Management:** uv

This is the setup for the FastAPI backend application, integrated with PostgreSQL and Redis.

## Prerequisites
Make sure you have [uv](https://github.com/astral-sh/uv) and [Docker Compose](https://docs.docker.com/compose/) installed on your system.

## Setup & Installation

1. Clone the repository and navigate to the project directory.
2. Create your local environment variables file by copying the sample:
```bash
  cp .env.sample .env
```
3. Sync the dependencies (`uv` will automatically create a `.venv` and install everything from `uv.lock`):
```bash
  uv sync
```

## Running Locally (Without Docker)

To start the FastAPI server with auto-reload enabled for local development:

```bash
  uv run uvicorn main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

## Running Tests

To execute the test suite using pytest, run:

```bash
  uv run pytest
```

## Running with Docker Compose (Recommended)

The application includes **PostgreSQL** and **Redis** managed via Docker Compose.

1. Build and start the API and databases in the background:
```bash
  docker compose up --build -d
```
The API will be available at `http://localhost:8000`.

2. To stop the running containers:
```bash
  docker compose down
```

3. The databases use Docker volumes (`postgres-data`, `redis-data`) to persist data. To completely wipe the data and restart, run:
```bash 
  docker compose down -v
```

## Database Configuration

* **PostgreSQL (Port 5432):** Connection is managed via `SQLAlchemy` (AsyncSession) and `asyncpg` in `app/core/database.py`.
* **Redis (Port 6379):** Connection is managed via `redis.asyncio` in `app/core/redis.py`.
* **Important:** Ensure your `.env` contains the correct credentials. When running via Docker, use `DB_HOST=postgresql` and `REDIS_HOST=redis`.

## Database Migrations (Alembic)

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations. All migration commands should be executed inside the running Docker container using `uv`.

### Create a New Migration
When you change your SQLAlchemy models (e.g., add a new table or column), generate a new migration script:

```bash
  docker compose exec back-end uv run alembic revision --autogenerate -m "Your descriptive message here"
```
*Note: The generated file will appear in the `alembic/versions` directory. If the file does not appear in your local IDE immediately, you can copy it from the container: `docker compose cp back-end:/app/alembic/versions/ ./alembic/`*

### Apply Migrations
To apply all pending migrations to the database, run:

```bash
  docker compose exec back-end uv run alembic upgrade head
```

### Rollback Migrations
If you need to undo the last applied migration:

```bash
  docker compose exec back-end uv run alembic downgrade -1
```

## Logging

The application includes a centralized logging system configured in `app/core/logger.py`. All HTTP requests and unhandled exceptions are automatically tracked via FastAPI middleware and exception handlers.

When running via Docker Compose, you can view the formatted logs in real-time using:
```bash
  docker compose logs -f back-end
```
