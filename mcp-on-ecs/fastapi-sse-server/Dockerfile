FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Set default environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
ENV MCP_SERVER_MODE=stdio
# API_KEY should be provided at runtime for security

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["python", "server.py"]
