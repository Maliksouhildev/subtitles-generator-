# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies including FFmpeg with libass and Arabic font libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fontconfig \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-liberation \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY core/ ./core/
COPY fonts/ ./fonts/
COPY web/ ./web/
COPY server.py cli.py ./

# Register bundled Arabic fonts with fontconfig
RUN fc-cache -fv /app/fonts

# Expose web interface port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
