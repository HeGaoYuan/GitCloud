#!/usr/bin/env python3
"""
Docker Image Recommendations for GitCloud
------------------------------------------
Provides base Docker images for different project types.
All images are pre-built and available on Docker Hub.
"""

from typing import Dict, Optional
from .cloud_service_spec import ProjectType


# GitCloud Docker Hub 配置
# 注意: 替换为你的 Docker Hub 用户名
DOCKER_HUB_USERNAME = "hegaoyuan"

# 基础镜像模板（使用 GitCloud 预构建镜像）
# 所有镜像都包含 Claude Code CLI 和常用开发工具
CLAUDE_CODE_BASE_IMAGES = {
    # Python 生态系统
    "python": {
        "image": f"{DOCKER_HUB_USERNAME}/python:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/python",
        "description": "Python 3.11 + Claude Code + 常用工具",
        "includes": [
            "Python 3.11",
            "pip, venv, pipenv",
            "git, curl, wget",
            "build-essential (gcc, g++, make)",
            "pytest, black, flake8",
            "Claude Code CLI"
        ],
        "size_mb": 250,
        "dockerfile_path": "../dockerfiles/python/Dockerfile"
    },

    # Node.js 生态系统
    "nodejs": {
        "image": f"{DOCKER_HUB_USERNAME}/nodejs:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/nodejs",
        "description": "Node.js 20 + Claude Code + 现代前端工具",
        "includes": [
            "Node.js 20 LTS",
            "npm, yarn, pnpm",
            "git, curl, wget",
            "Python 3 (for node-gyp)",
            "pm2, http-server",
            "Claude Code CLI"
        ],
        "size_mb": 300,
        "dockerfile_path": "../dockerfiles/nodejs/Dockerfile"
    },

    # Go 生态系统
    "golang": {
        "image": f"{DOCKER_HUB_USERNAME}/golang:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/golang",
        "description": "Go 1.21 + Claude Code + 常用工具",
        "includes": [
            "Go 1.21",
            "git, make, gcc",
            "Claude Code CLI"
        ],
        "size_mb": 200,
        "dockerfile_path": "../dockerfiles/golang/Dockerfile"
    },

    # Java 生态系统
    "java": {
        "image": f"{DOCKER_HUB_USERNAME}/java:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/java",
        "description": "OpenJDK 17 + Maven + Gradle + Claude Code",
        "includes": [
            "OpenJDK 17",
            "Maven 3.9",
            "Gradle 8.x",
            "git, curl, wget",
            "Claude Code CLI"
        ],
        "size_mb": 350,
        "dockerfile_path": "../dockerfiles/java/Dockerfile"
    },

    # 机器学习 - CPU 版本
    "ml_cpu": {
        "image": f"{DOCKER_HUB_USERNAME}/ml-cpu:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/ml-cpu",
        "description": "Python 3.11 + ML 库 (CPU) + Claude Code",
        "includes": [
            "Python 3.11",
            "numpy, pandas, scikit-learn",
            "tensorflow-cpu, pytorch (CPU)",
            "jupyter, matplotlib",
            "Claude Code CLI"
        ],
        "size_mb": 2000,
        "dockerfile_path": "../dockerfiles/ml-cpu/Dockerfile"
    },

    # 机器学习 - GPU 版本
    "ml_gpu": {
        "image": f"{DOCKER_HUB_USERNAME}/ml-gpu:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/ml-gpu",
        "description": "CUDA 12.1 + cuDNN 8 + Python + ML 库 + Claude Code",
        "includes": [
            "CUDA 12.1",
            "cuDNN 8",
            "Python 3.11",
            "PyTorch (GPU), TensorFlow (GPU)",
            "transformers, accelerate",
            "Claude Code CLI"
        ],
        "size_mb": 8000,
        "dockerfile_path": "../dockerfiles/ml-gpu/Dockerfile"
    },

    # 数据处理
    "data_processing": {
        "image": f"{DOCKER_HUB_USERNAME}/data-processing:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/data-processing",
        "description": "Python 3.11 + 数据处理库 + Claude Code",
        "includes": [
            "Python 3.11",
            "pandas, numpy, polars",
            "dask, pyarrow",
            "sqlalchemy, pymongo",
            "Claude Code CLI"
        ],
        "size_mb": 400,
        "dockerfile_path": "../dockerfiles/data-processing/Dockerfile"
    },

    # Rust 生态系统
    "rust": {
        "image": f"{DOCKER_HUB_USERNAME}/rust:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/rust",
        "description": "Rust 1.75 + Cargo + Claude Code",
        "includes": [
            "Rust 1.75",
            "Cargo",
            "git, build tools",
            "Claude Code CLI"
        ],
        "size_mb": 1000,
        "dockerfile_path": "../dockerfiles/rust/Dockerfile"
    },

    # 多语言通用镜像
    "polyglot": {
        "image": f"{DOCKER_HUB_USERNAME}/polyglot:latest",
        "dockerhub_url": f"https://hub.docker.com/r/{DOCKER_HUB_USERNAME}/polyglot",
        "description": "Ubuntu 22.04 + Python + Node.js + Go + Claude Code",
        "includes": [
            "Python 3.11",
            "Node.js 20",
            "Go 1.21",
            "git, docker, kubectl",
            "Claude Code CLI"
        ],
        "size_mb": 1500,
        "dockerfile_path": "../dockerfiles/polyglot/Dockerfile"
    }
}


# 项目类型到镜像的映射
PROJECT_TYPE_TO_IMAGE: Dict[ProjectType, str] = {
    # Web 应用类
    ProjectType.WEB_FRONTEND: "nodejs",
    ProjectType.WEB_BACKEND: "python",
    ProjectType.WEB_FULLSTACK: "nodejs",
    ProjectType.WEB_STATIC: "nodejs",

    # 数据库应用类
    ProjectType.DATABASE_APP: "python",

    # 微服务架构类
    ProjectType.MICROSERVICES: "polyglot",
    ProjectType.SERVERLESS: "python",

    # AI/ML 类
    ProjectType.ML_TRAINING: "ml_gpu",
    ProjectType.ML_INFERENCE: "ml_cpu",
    ProjectType.DEEP_LEARNING: "ml_gpu",
    ProjectType.LLM_SERVICE: "ml_gpu",

    # 数据处理类
    ProjectType.DATA_ETL: "data_processing",
    ProjectType.DATA_ANALYTICS: "data_processing",
    ProjectType.BIG_DATA: "data_processing",
    ProjectType.STREAM_PROCESSING: "java",

    # 移动后端类
    ProjectType.MOBILE_BACKEND: "python",
    ProjectType.IOT_BACKEND: "python",

    # 游戏类
    ProjectType.GAME_SERVER: "polyglot",

    # 企业应用类
    ProjectType.CRM_ERP: "java",
    ProjectType.CONTENT_MANAGEMENT: "python",
    ProjectType.ECOMMERCE: "python",

    # 开发工具类
    ProjectType.CI_CD: "polyglot",
    ProjectType.MONITORING: "golang",

    # 通用类
    ProjectType.GENERAL: "polyglot",
    ProjectType.UNKNOWN: "polyglot",
}


def get_recommended_image(
    project_type: ProjectType,
    gpu_required: bool = False,
    detected_language: Optional[str] = None
) -> Dict:
    """
    获取推荐的 Docker 镜像

    Args:
        project_type: 项目类型
        gpu_required: 是否需要 GPU (保留用于未来扩展)
        detected_language: 检测到的主要编程语言 (如 'golang', 'nodejs' 等)

    Returns:
        镜像信息字典，包含 image, description, includes, dockerhub_url
    """
    # Alpha version: only support nodejs and golang
    # GPU support will be added in future versions

    # 如果检测到具体编程语言，优先使用语言特定镜像
    if detected_language:
        # 语言到镜像的映射 (Alpha: only nodejs and golang)
        language_to_image = {
            'golang': 'golang',
            'go': 'golang',
            'nodejs': 'nodejs',
            'node': 'nodejs',
            'javascript': 'nodejs',
            'typescript': 'nodejs',
        }

        image_key = language_to_image.get(detected_language.lower())

        # 如果映射表中没有找到，返回默认
        if not image_key or image_key not in CLAUDE_CODE_BASE_IMAGES:
            # Default to nodejs for web projects, golang for others
            if 'web' in project_type.value.lower() or 'frontend' in project_type.value.lower():
                image_key = 'nodejs'
            else:
                image_key = 'golang'
    else:
        # 根据项目类型获取镜像 (default to nodejs or golang)
        if 'web' in project_type.value.lower() or 'frontend' in project_type.value.lower():
            image_key = 'nodejs'
        else:
            image_key = 'golang'

    return CLAUDE_CODE_BASE_IMAGES[image_key]


def get_docker_run_command(project_type: ProjectType, gpu_required: bool = False) -> str:
    """
    生成 Docker run 命令

    Args:
        project_type: 项目类型
        gpu_required: 是否需要 GPU

    Returns:
        Docker run 命令字符串
    """
    image_info = get_recommended_image(project_type, gpu_required)
    image = image_info['image']

    base_cmd = "docker run -it -v $(pwd):/workspace"

    if gpu_required:
        base_cmd = "docker run --gpus all -it -v $(pwd):/workspace"

    # 添加端口映射
    if "nodejs" in image:
        base_cmd += " -p 3000:3000"
    elif "ml" in image or "jupyter" in image:
        base_cmd += " -p 8888:8888"
    else:
        base_cmd += " -p 8000:8000"

    base_cmd += f" {image}"

    return base_cmd


def list_all_images() -> Dict[str, Dict]:
    """
    列出所有可用的基础镜像

    Returns:
        所有镜像的信息字典
    """
    return CLAUDE_CODE_BASE_IMAGES


def get_image_pull_commands() -> Dict[str, str]:
    """
    获取所有镜像的 pull 命令

    Returns:
        镜像名称到 pull 命令的映射
    """
    return {
        key: f"docker pull {info['image']}"
        for key, info in CLAUDE_CODE_BASE_IMAGES.items()
    }


if __name__ == "__main__":
    # 示例：打印所有镜像
    print("GitCloud Docker Images (Pre-built on Docker Hub)\n")
    print(f"Docker Hub Username: {DOCKER_HUB_USERNAME}\n")
    print("="*70)

    for key, info in CLAUDE_CODE_BASE_IMAGES.items():
        print(f"\n## {key}")
        print(f"   Image: {info['image']}")
        print(f"   Size: ~{info['size_mb']}MB")
        print(f"   Docker Hub: {info['dockerhub_url']}")
        print(f"   Description: {info['description']}")
        print(f"   Pull command: docker pull {info['image']}")

    print("\n" + "="*70)
    print("\nTo use these images:")
    print("1. Pull the image: docker pull gitcloud/python:latest")
    print("2. Run container: docker run -it -v $(pwd):/workspace gitcloud/python:latest")
    print("3. Use Claude Code inside container to setup your project")
