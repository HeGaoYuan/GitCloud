FROM ubuntu:22.04

# Install common Linux utilities
RUN apt-get update && \
    apt-get install -y \
    wget \
    curl \
    git \
    vim \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Go
ENV GO_VERSION=1.23.1
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

# Install Node.js (required for claude-code)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install claude-code
RUN npm install -g @anthropic-ai/claude-code