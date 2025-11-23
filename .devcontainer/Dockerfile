FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    postgresql-client \
    libpq-dev \
    build-essential \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --upgrade pip setuptools wheel \
    && pip install black flake8 isort pylint pytest pytest-django

# Set working directory
WORKDIR /workspaces/Floor-Management-System

# Install Python dependencies (will be overridden by postCreateCommand)
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt || true
