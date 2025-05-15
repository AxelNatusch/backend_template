# Python Docker base image alternatives:

# Standard Python Base Images
# ===========================

# Option 1: Standard Debian-based image (larger but more packages pre-installed)
FROM python:3.12-bookworm
# Pros: Full Debian environment, all dependencies included, best compatibility
# Cons: Larger image size (~150MB+)

# Option 2: Ubuntu-based Python image (newest LTS release)
# FROM python:3.12-ubuntu-24.04
# Pros: Latest Ubuntu LTS with security updates, ~10% faster Python performance
# Cons: Larger image size, similar to standard Debian-based image

# Minimal Python Base Images
# =========================

# Option 3: Slim variant (current choice - good balance of compatibility and size)
# FROM python:3.12-slim-bookworm
# Pros: Reduced size, maintains compatibility, familiar Debian environment
# Cons: Some system packages removed, may need to install dependencies


# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download and run the uv installer (latest version)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

ADD . /app

WORKDIR /app

RUN uv sync --frozen

CMD ["uv", "run", "app.py"]

EXPOSE 8000
