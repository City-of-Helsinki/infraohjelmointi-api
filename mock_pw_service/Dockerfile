FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install flask

# Create data directory for persistence
RUN mkdir -p /data

# Copy application
COPY app.py .

# Expose port
EXPOSE 8080

# Create volume for data persistence
VOLUME ["/data"]

# Run the application
CMD ["python", "app.py"]
