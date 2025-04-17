FROM python:3.11-slim

WORKDIR /app

# Install curl and any required tools
RUN apt-get update && apt-get install -y curl build-essential

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | bash

# ✅ Add uv to PATH (correct directory is .local/bin)
ENV PATH="/root/.local/bin:$PATH"

# Copy your project
COPY pyproject.toml .
COPY resolve_conflicts/ ./resolve_conflicts

# Install deps from pyproject.toml using uv
RUN uv pip install .

ENTRYPOINT ["python", "resolve_conflicts/main.py"]
