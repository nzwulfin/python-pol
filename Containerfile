# Stage 1: Base Image from Red Hat UBI
FROM registry.access.redhat.com/ubi9/python-311:latest AS base

# Explicitly switch to root user to perform privileged operations
USER root

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Create a non-root user and group for the application
# Using a different UID/GID to avoid conflict with existing users in the base image.
RUN groupadd -r -g 1005 appgroup && \
    useradd -r -u 1005 -g 1005 -d /app -s /sbin/nologin -c "Application User" appuser
    # Note: using GID 1005 directly in useradd for clarity, or you can use -g appgroup if groupadd with GID 1005 succeeded.

# Copy requirements.txt first to leverage Docker layer caching.
COPY requirements.txt .

# Install Python dependencies as root.
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container.
# Ensure ownership is set to the non-root user (appuser with UID 1005).
COPY --chown=appuser:appgroup . .

# Switch to the non-root user for runtime and subsequent commands
USER appuser

# Expose the port Gunicorn will run on
EXPOSE 8000

# Define the command to run the application using Gunicorn
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8000", "app:app"]
