# Use a slim Python image for efficiency on the NAS
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the files needed for App 1
COPY app.py .
COPY casino_stayers_clustered.csv .
COPY phase2_persona_migration_scored.csv .
COPY phase2_host_queue.csv .

# Expose Streamlit's default port
EXPOSE 8501

# Run the app with DDNS/WebSocket stability flags
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]