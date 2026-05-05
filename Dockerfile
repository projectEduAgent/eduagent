# Dockerfile
# ─────────────────────────────────────────────────────────────
# Builds the EduAgent Streamlit app image.
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached unless requirements.txt changes).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code.
COPY . .

EXPOSE 8501

# --server.fileWatcherType none  → disables file-watcher warnings
# --server.address 0.0.0.0      → makes the app reachable outside the container
CMD ["streamlit", "run", "ui/app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.fileWatcherType=none"]
