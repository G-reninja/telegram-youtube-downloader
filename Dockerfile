# Use official Python 3.11 lightweight image
FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set FFMPEG_PATH to system ffmpeg binary
ENV FFMPEG_PATH=ffmpeg

# Run the Telegram bot
CMD ["python", "src/bot.py"]
