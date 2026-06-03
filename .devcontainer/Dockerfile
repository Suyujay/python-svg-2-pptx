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

# Install python-pptx, testing tools, and other required python packages
RUN pip install --no-cache-dir python-pptx pytest pytest-cov

# Set default user
USER vscode
