# Backend Template

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![FastAPI Version](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

## Project Overview
### Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [SQLLite](https://www.sqlite.org) as the SQL database for Development (easy extendable to any other Relational Database like Postgresql).
- 🐋 [Docker](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- ✅ Tests with [Pytest](https://pytest.org).


**Backend Template** (v0.1.0) is a robust and feature-rich backend service foundation, built with Python and [FastAPI](https://fastapi.tiangolo.com/). It provides a comprehensive starting point for developing modern web APIs, with a strong emphasis on authentication, developer experience, and best practices.

This template is designed to be easily extensible, allowing developers to quickly build upon its core functionalities to create sophisticated backend applications.

## Core Features

This template comes packed with essential features to accelerate your development:

### Authentication & Authorization
*   **JWT-based Authentication:** Secure user registration (admin-initiated), login (username/password), and token refresh mechanisms.
*   **API Key Authentication:** Support for API key-based access to protected endpoints.
*   **User Context:** Endpoints to retrieve details of the currently authenticated user (via JWT or API Key).
*   **Admin-Protected Routes:** Example of restricting access to certain operations (e.g., user registration) to admin users.

### API Key Management
*   **Full Lifecycle Management:** Authenticated users can create, list, revoke (by key or ID), and permanently delete their API keys.
*   **Key Naming & Expiry:** Support for naming API keys for better organization and setting optional expiration dates.

### Database
*   **ORM with SQLModel:** Modern, intuitive data modeling and interaction using [SQLModel](https://sqlmodel.tiangolo.com/), which combines Pydantic and SQLAlchemy.
*   **Database Migrations with Alembic:** Robust schema migration management using [Alembic](https://alembic.sqlalchemy.org/), allowing for easy database evolution.

### Developer Experience (DX) & Operations
*   **`uv` Package Management:** Ultra-fast and efficient dependency management with [uv](https://github.com/astral-sh/uv).
*   **Environment-based Configuration:** Flexible application settings managed via `.env` files (leveraging Pydantic for validation).
*   **Structured Logging:** Comprehensive logging setup with console and file outputs (including JSONL format), configurable log levels, and easy integration into services.
*   **Dockerized:** Comes with a `Dockerfile` for easy containerization and deployment.
*   **CORS Pre-configured:** Cross-Origin Resource Sharing (CORS) middleware is set up for easy frontend integration.
*   **Hot Reloading:** Development server (`uv run app.py`) supports automatic reloading on code changes.

### Code Quality & Structure
*   **Modular Design:** Well-organized project structure with a clear separation of concerns (e.g., `src/domains`, `src/core`).
*   **Dependency Injection:** FastAPI's dependency injection system is utilized for managing dependencies like database sessions and current user context.
*   **Asynchronous Support:** Built with `async` and `await` for high-performance I/O operations.
*   **Clear API Versioning:** API endpoints are versioned (e.g., `/v1/...`).

---

## Project Structure Overview

A brief overview of the key directories and files:

- `/.venv/`: Virtual environment managed by `uv` (typically not committed).
- `/logs/`: Application log files (primarily for development, also not typically committed).
- `/migrations/`: Alembic database migration scripts and environment configuration.
    - `/versions/`: Individual migration script files.
    - `env.py`: Alembic runtime environment configuration.
- `/src/`: Contains the core application source code.
    - `/api/`: API layer, including endpoint definitions and routing logic.
        - `/dependencies/`: Reusable API dependencies (e.g., for authentication).
        - `/routers/`: FastAPI routers for different API modules or domains.
    - `/core/`: Core application logic, configuration, and utilities.
        - `/auth/`: Authentication-specific core components (e.g., password hashing).
        - `/config/`: Application settings management (e.g., `settings.py`).
        - `/db/`: Database connection, session management, and initialization logic.
        - `/exceptions/`: Custom application exceptions.
        - `/logging/`: Logging configuration, formatters, and handlers.
    - `/domains/`: Business logic and models for different application domains (e.g., `auth`).
        - `/auth/`: Specific logic, models, and API definitions for the authentication domain.
            - `/api/`: FastAPI routers and request/response models for authentication.
            - `/models/`: SQLModel/Pydantic models for authentication (e.g., `User`, `APIKey`).
            - `/services/`: Business logic services for authentication.
- `/tests/`: Automated tests for the application, mirroring the `src/` structure.
- `app.py`: Main entry point to run the Uvicorn server for the FastAPI application.
- `alembic.ini`: Configuration file for Alembic database migrations.
- `Dockerfile`: Instructions for building the Docker image for the application.
- `example.env`: Template for environment variables.
- `LICENSE`: Project license file.
- `pyproject.toml`: Project metadata and dependencies, used by `uv`.
- `pytest.ini`: Configuration for `pytest`.
- `README.md`: This file!
- `uv.lock`: Lock file generated by `uv` for reproducible dependencies.

---

## Package Management

This project uses [uv](https://github.com/astral-sh/uv) instead of pip for Python package management. uv is significantly faster than pip and provides better dependency resolution.

### Getting Started

1. Install uv in your shell - see installation options on the [uv GitHub page](https://github.com/astral-sh/uv) or [uv Docu page](https://docs.astral.sh/uv/getting-started/installation/)

2. Create and activate a virtual environment:
    - go to root directory of this project
   ```bash
   uv sync
   # on Linux/Mac
   source .venv/bin/activate  
   # on Windows: 
   source .venv\Scripts\activate
   ```

### Common Commands

```bash
# run a script
uv run <python_file>

# Add a package
uv add <package_name>

# Remove a package
uv remove <package_name>

# sync the projects dependencies with the environment
uv sync

# install a specific python version
uv python install 3.12

# connect your shell to the virtual environment
source .venv/bin/activate # On Linux/Mac
source .venv/Scripts/activate  # On Windows
```

## Development

### Environment Setup

Follow these steps to set up your local development environment:

1.  **Create `.env` File:**
    Copy the `example.env` file to a new file named `.env` in the project root.
    ```
    cp example.env .env
    ```
    Update the variables in `.env` as needed. For local development, the default `DATABASE_URL=sqlite:///./test.db` is usually sufficient.
    ```
    # .env (example)
    # Required
    DATABASE_URL=sqlite:///./test.db  # Default SQLite URL for development
    ENVIRONMENT=development  # Sets the application environment
    
    # Optional
    CORS_ORIGINS=http://localhost:3000,http://localhost:8000  # Allowed origins for CORS
    ```

2.  **Install Dependencies:**
    Ensure `uv` is installed (see [Package Management](#package-management)). Then, install project dependencies:
    ```bash
    uv sync
    ```

3.  **Activate Virtual Environment:**
    ```bash
    # on Linux/Mac
    source .venv/bin/activate
    # on Windows
    source .venv\Scripts\activate
    ```

4.  **Initialize Database Schema (Alembic):**
    Before running the application for the first time, or if you've pulled changes that include new migrations, you need to apply database migrations. This will create the SQLite file (if it doesn't exist) and bring the schema up to date:
    ```bash
    alembic upgrade head
    ```
    *(For more details on database migrations, see the [Database Migrations (Alembic)](#database-migrations-alembic) section below.)*

### Running the Application

Once your environment is set up and the database is initialized:

1.  **Start the Development Server:**
    ```bash
    uv run app.py
    ```
    The FastAPI application will start on `http://localhost:8000` (or the port configured in your `.env` or application settings). The server will typically have hot-reload enabled, meaning changes to your code will automatically restart the server.

### API Documentation

Once the application is running, you can access:
- Swagger UI: http://localhost:8000/docs

## Docker

### Prerequisites

- Docker must be installed on your system. For installation instructions, visit the [Docker installation page](https://docs.docker.com/engine/install/).

### Building and Running

1. Build the Docker image:
   ```bash
   docker build -t backend_template .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 backend_template 
   ```

3. To run with environment variables:
   ```bash
   docker run -p 8000:8000 -e DATABASE_URL=sqlite:///.test.db backend_template 
   ```

   You can add multiple environment variables using the `-e` flag for each variable.

## Database Migrations (Alembic)

This project uses Alembic to manage database schema migrations. Alembic provides a version control system for your database schema, allowing you to track and apply changes systematically.

The Alembic environment is configured in `alembic.ini` and `migrations/env.py`. Migration scripts are stored in the `migrations/versions/` directory.

### Initial Setup (Covered in Development Section)

The initial database setup (creating the database and applying all migrations) is part of the [Environment Setup](#environment-setup) instructions. Ensure you have run `alembic upgrade head` after setting up your environment and before running the application for the first time.

### Workflow for Schema Changes

When you need to change the database schema (e.g., add a table, add a column, change a data type) after modifying your `SQLModel` definitions in the Python code (`src/domains/.../models/`), follow these steps:

1.  **Update Models:** Modify your `SQLModel` classes in the relevant `src/domains/.../models/*.py` files.
    *   **Important:** If you add a *new* model file, you **must** import it within `migrations/env.py` near the other model imports. This ensures Alembic's autogenerate feature can detect the new table.

2.  **Generate Migration Script:** Run the Alembic command to automatically detect changes between your models and the current database state (as tracked by Alembic) and generate a new migration script:
    ```bash
    alembic revision --autogenerate -m "Your descriptive message about the change"
    ```
    *Replace `"Your descriptive message..."` with a short summary of the schema changes (e.g., `"Add description column to User model"`).* 
    *This will create a new file in `migrations/versions/`.*

3.  **Review the Generated Script:** **This is a critical step!** Open the newly generated migration script in `migrations/versions/`. Carefully review the `upgrade()` and `downgrade()` functions. Autogenerate is helpful but not perfect; it might miss certain changes (like server defaults, complex constraints) or generate things you didn't intend. Modify the script manually if needed.
Since we are using `SQLModel` in the project, the import for `SQLModel` needs most-likely to be added manuall, because normally it expectes SQLAlchemy.

4.  **Apply the Migration:** Run the upgrade command to apply the new migration script (and any other pending ones) to your database:
    ```bash
    alembic upgrade head
    ```
    *`head` refers to the latest revision.* 
    *This command executes the `upgrade()` function in the new migration script(s).*

### Common Alembic Commands

Here are some useful Alembic commands:

*   `alembic current`: Show the current revision the database is migrated to.
*   `alembic history`: List all migration scripts and indicate the current position.
*   `alembic upgrade <revision>`: Upgrade the database to a specific revision.
*   `alembic downgrade <revision>`: Downgrade the database to a specific revision (e.g., `alembic downgrade -1` to revert the last migration).
*   `alembic stamp <revision>`: Mark the database as being at a specific revision *without* running the migration scripts (useful for syncing Alembic's state with an existing database).

**Important:** Always ensure your database is backed up before running potentially destructive migration operations, especially downgrades.

