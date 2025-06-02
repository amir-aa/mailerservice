FROM python:3.11-slim

# Create non-root user and directories
RUN useradd -m mailuser && \
    mkdir -p /app /data && \
    chown mailuser:mailuser /app /data && \
    chmod 755 /data

WORKDIR /app


RUN apt-get update && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY --chown=mailuser requirements.txt .
RUN pip install --upgrade pip && pip install pymysql && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY --chown=mailuser . .

# Switch to non-root user
USER mailuser

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:5004", "--workers", "2", "wsgi:app"]
