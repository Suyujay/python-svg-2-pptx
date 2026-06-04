FROM python:3.11-alpine

# Install development tools and C dependencies required by python-pptx (lxml, Pillow)
RUN apk add --no-cache \
    git \
    bash \
    build-base \
    libxml2-dev \
    libxslt-dev \
    jpeg-dev \
    zlib-dev

# Create a non-root user that VS Code can use
RUN adduser -D vscode

# Copy requirements file and install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Set default user
USER vscode
