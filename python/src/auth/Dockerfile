# Use an official lightweight Python image based on Debian Bullseye
FROM python:3.10-slim-bullseye

# Install system dependencies required for building Python packages
# and for MySQL/MariaDB client support
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        build-essential \
        default-libmysqlclient-dev \
        libssl-dev \
        libffi-dev \
        gcc \
        pkg-config \
        libmariadb-dev && \
    pip install --no-cache-dir --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app

# Install Python dependencies from the requirements file
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire project into the container
COPY . /app

# Expose the application port (Flask default)
EXPOSE 5000

# Set the default command to run your application
CMD ["python", "server.py"]
