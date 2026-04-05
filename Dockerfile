FROM python:3.11-slim

# Install ffmpeg (required for audio streaming)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libssl-dev \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]