FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required by telethon cryptography
RUN apt-get update && apt-get install -y gcc sqlite3 libsqlite3-dev --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Add newly added deps directly since user requested missing ones appended
RUN pip install --no-cache-dir flask-cors telethon
RUN pip install gunicorn
# Copy all project files
COPY . .


# Command to run the application using gunicorn for better production performance
CMD sh -c "gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 main:app"