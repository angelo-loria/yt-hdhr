FROM python:3.12-slim

WORKDIR /app

# Install ffmpeg (needed by streamlink for some streams)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir flask streamlink yt-dlp

# Copy application code
COPY youtube-live.py .

# Default directory for .m3u files
RUN mkdir -p /data
ENV M3U_DIR=/data

EXPOSE 6095

CMD ["python", "youtube-live.py"]
