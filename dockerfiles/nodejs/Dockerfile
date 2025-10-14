FROM ubuntu:22.04

# 更新包列表并安装常见 Linux 命令和依赖
RUN apt-get update && \
    apt-get install -y \
    curl \
    wget \
    git \
    vim \
    net-tools \
    mysql-client-core-8.0 \
    gnupg \
    ca-certificates

# Install Node.js (required for claude-code)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install claude-code
RUN npm install -g @anthropic-ai/claude-code