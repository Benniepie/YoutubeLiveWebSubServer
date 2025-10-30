# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .

# Copy OAuth2 token (REQUIRED for YouTube API)
# Generate locally: python youtube_metadata.py <video_id>
# Then copy token.pickle to server before building Docker image
COPY token.pickle .

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/notifications.db

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/', timeout=5)"

# Run the application
CMD ["python", "websub_server.py"]
