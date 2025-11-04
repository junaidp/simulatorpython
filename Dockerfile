# ============================
# Base Image
# ============================
FROM python:3.11-slim

# Set working directory
WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
 && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt gunicorn


COPY . .


RUN mkdir -p instance


ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Start using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
