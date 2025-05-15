# backend template

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

1. Create a `.env` file in the project root with the following variables:
   ```
   # Required
   DATABASE_URL=sqlite:///./test.db  # Default SQLite URL for development
   ENVIRONMENT=development  # Sets the application environment
   
   # Optional
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000  # Allowed origins for CORS
   
   # SEQLOG Config
    SEQ_URL=""
    SEQ_API_KEY=""
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   # on Linux/Mac
   source .venv/bin/activate
   # on Windows
   source .venv\Scripts\activate
   ```

### Running the Application

Start the development server with hot-reload:

```bash
uv run app.py
```

The FastAPI application will start on http://localhost:8000 with automatic reload on code changes.

### API Documentation

Once the application is running, you can access:
- Swagger UI: http://localhost:8000/docs

## Docker

### Prerequisites

- Docker must be installed on your system. For installation instructions, visit the [Docker installation page](https://docs.docker.com/engine/install/).

### Building and Running

1. Build the Docker image:
   ```bash
   docker build -t docu_read .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 docu_read
   ```

3. To run with environment variables:
   ```bash
   docker run -p 8000:8000 -e DATABASE_URL=sqlite:///.test.db docu_read
   ```

   You can add multiple environment variables using the `-e` flag for each variable.

## Database Migrations (Alembic)

This project uses Alembic to manage database schema migrations. Alembic provides a version control system for your database schema, allowing you to track and apply changes systematically.

The Alembic environment is configured in `alembic.ini` and `migrations/env.py`. Migration scripts are stored in the `migrations/versions/` directory.

### Initial Local Setup (SQLite)

For local development, you will typically use a new SQLite database file (`test.db` by default, defined in `.env`). To initialize this database with the current schema:

1.  **Ensure `.env` is configured:** Make sure your `.env` file exists and `DATABASE_URL` points to your desired SQLite file (e.g., `DATABASE_URL=sqlite:///./test.db`).
2.  **Activate Virtual Environment:** Make sure your environment is active.
3.  **Run Initial Migration:** Execute the following command. This will create the SQLite file (if it doesn't exist) and apply all existing migration scripts to bring the schema up to date:
    ```bash
    alembic upgrade head
    ```

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
Since we are using SQLModel, the import for that needs most-likely to be added manually.

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

