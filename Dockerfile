FROM python:3.11-slim

WORKDIR /app

# Install curl and required build tools
RUN apt-get update && apt-get install -y curl build-essential && \
    curl -LsSf https://astral.sh/uv/install.sh | bash

# Add uv to PATH for all future layers
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY resolve_conflicts/ ./resolve_conflicts

# Install dependencies using uv from pyproject.toml
RUN uv pip install .

ENTRYPOINT ["python", "resolve_conflicts/main.py"]
