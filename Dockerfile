FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Copy your project files
COPY pyproject.toml .
COPY resolve_conflicts/ ./resolve_conflicts

# Install deps from pyproject.toml
RUN uv pip install .

ENTRYPOINT ["python", "resolve_conflicts/main.py"]
