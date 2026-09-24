FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Never run as root.
RUN useradd --system --uid 10001 proxy
USER proxy

ENV PORT=8080
EXPOSE 8080
# Long timeout: a Veo video with "wait": true can take a few minutes.
CMD ["sh", "-c", "gunicorn --worker-tmp-dir /dev/shm -w 2 --threads 4 -b 0.0.0.0:${PORT} --timeout 600 app:app"]
