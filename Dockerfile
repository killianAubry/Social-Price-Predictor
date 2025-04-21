FROM python:3.11-slim-buster

# Install necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy your application code
COPY . .

EXPOSE 5001

# Set the entry point for your application
CMD ["python", "app.py"]
