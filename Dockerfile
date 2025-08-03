
# Use the official lightweight Python image
FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files first (better caching)
COPY ./app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files into the container
COPY app/ .

# Expose Streamlit default port
EXPOSE 8501

# Streamlit settings to allow external access
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run Streamlit app
CMD ["streamlit", "run", "app.py"]



#CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

