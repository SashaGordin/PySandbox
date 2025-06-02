# Use a multi-stage build to include nsjail in the final image
# Stage 1: Build nsjail
FROM debian:bookworm-slim AS nsjail-builder

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    protobuf-compiler \
    libprotobuf-dev \
    libprotobuf32 \
    libnl-3-dev \
    libnl-genl-3-dev \
    libnl-route-3-dev \
    libcap-dev \
    autoconf \
    bison \
    flex \
    libtool \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/google/nsjail.git /nsjail \
    && cd /nsjail \
    && make \
    && mv nsjail /usr/local/bin/nsjail

# Stage 2: Final image with nsjail and Cloud Run v2 execution environment
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m sandboxuser

# Copy nsjail from the builder stage
COPY --from=nsjail-builder /usr/local/bin/nsjail /usr/local/bin/nsjail

# Install dependencies
RUN apt-get update && apt-get install -y \
    libprotobuf-dev \
    libprotobuf32 \
    libnl-3-dev \
    libnl-genl-3-dev \
    libnl-route-3-dev \
    libcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change to non-root user
USER sandboxuser

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]