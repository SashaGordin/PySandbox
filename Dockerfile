# Use a lightweight Python base image
FROM python:3.12-slim

# Install system dependencies for pandas, numpy, and nsjail build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    flex \
    bison \
    wget \
    ca-certificates \
    libprotobuf-dev \
    protobuf-compiler \
    pkg-config \
    libtool \
    automake \
    g++ \
    libcap-dev \
    libseccomp-dev \
    libnl-3-dev \
    libnl-route-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build and install nsjail
RUN git clone https://github.com/google/nsjail.git /opt/nsjail \
    && cd /opt/nsjail \
    && make \
    && cp nsjail /usr/local/bin/nsjail

# Copy app code
COPY app.py .

# Expose port 8080
EXPOSE 8080

# Run the Flask app
CMD ["python", "app.py"]