FROM ubuntu:22.04

# 设置 apt 源为阿里云镜像，以加速在中国大陆的构建
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list

# 更新包列表并安装常见 Linux 命令和依赖
RUN apt-get update && \
    apt-get install -y \
    curl \
    wget \
    git \
    vim \
    gnupg \
    ca-certificates

# 安装 Node.js（使用 NodeSource 仓库，安装 LTS 版本 20.x）
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# 设置 npm  registry 为中国镜像，以加速包下载
RUN npm config set registry https://registry.npmmirror.com

# 安装 claude-code
RUN npm install -g @anthropic-ai/claude-code

# 设置工作目录（可选）
WORKDIR /app