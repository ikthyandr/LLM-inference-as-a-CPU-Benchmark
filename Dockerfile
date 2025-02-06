# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Set environment variables (optional, but good practice)
ENV DEBIAN_FRONTEND=noninteractive

# Update the package index and install prerequisites: ansible and python3-pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    python3 \
    python3-pip \
    ansible \
    sshpass \
    git

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install the Python dependencies from requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Optional: Clean up apt cache to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
