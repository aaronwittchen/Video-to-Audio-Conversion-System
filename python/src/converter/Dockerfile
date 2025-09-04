FROM python:3.10-slim-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        build-essential \
        ffmpeg \
        libssl-dev \
        libffi-dev \
        gcc \
        pkg-config \
        libmariadb-dev && \
    pip install --no-cache-dir --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Verify ffmpeg installation
RUN ffmpeg -version
RUN python -c "import ffmpeg; print('ffmpeg-python installed successfully')"

COPY . /app

CMD ["python", "consumer.py"]