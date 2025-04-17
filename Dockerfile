FROM python:3.11-slim

WORKDIR /app

# Install curl and build tools
RUN apt-get update && apt-get install -y curl build-essential

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | bash

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy your project files
COPY pyproject.toml .
COPY resolve_conflicts/ ./resolve_conflicts

# ✅ Install dependencies into system environment using uv
RUN uv pip install --system .

ENTRYPOINT ["python", "resolve_conflicts/main.py"]
