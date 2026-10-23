FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Build frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install && npm run build

# Copy backend
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY frontend/dist ./backend/staticfiles

# Collect static files
RUN cd backend && python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "truck_routing.wsgi:application", "--bind", "0.0.0.0:8000"]