#!/usr/bin/env python3
"""
Cloud Service Specification Module for GitCloud
------------------------------------------------
Defines cloud service requirements and project type classifications.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class ProjectType(Enum):
    """
    全面的项目类型分类（基于软件行业常见分类）
    """
    # Web 应用类
    WEB_FRONTEND = "web_frontend"  # 前端应用（React, Vue, Angular）
    WEB_BACKEND = "web_backend"  # 后端 API 服务
    WEB_FULLSTACK = "web_fullstack"  # 全栈应用
    WEB_STATIC = "web_static"  # 静态网站

    # 数据库应用类
    DATABASE_APP = "database_app"  # 需要数据库的应用

    # 微服务架构类
    MICROSERVICES = "microservices"  # 微服务架构
    SERVERLESS = "serverless"  # Serverless 应用

    # AI/ML 类
    ML_TRAINING = "ml_training"  # 机器学习训练
    ML_INFERENCE = "ml_inference"  # 机器学习推理
    DEEP_LEARNING = "deep_learning"  # 深度学习
    LLM_SERVICE = "llm_service"  # 大语言模型服务

    # 数据处理类
    DATA_ETL = "data_etl"  # 数据 ETL
    DATA_ANALYTICS = "data_analytics"  # 数据分析
    BIG_DATA = "big_data"  # 大数据处理（Spark, Hadoop）
    STREAM_PROCESSING = "stream_processing"  # 流处理（Kafka, Flink）

    # 移动后端类
    MOBILE_BACKEND = "mobile_backend"  # 移动应用后端
    IOT_BACKEND = "iot_backend"  # IoT 设备后端

    # 游戏类
    GAME_SERVER = "game_server"  # 游戏服务器

    # 企业应用类
    CRM_ERP = "crm_erp"  # CRM/ERP 系统
    CONTENT_MANAGEMENT = "content_management"  # CMS 内容管理系统
    ECOMMERCE = "ecommerce"  # 电商平台

    # 开发工具类
    CI_CD = "ci_cd"  # CI/CD 系统
    MONITORING = "monitoring"  # 监控系统

    # 通用类
    GENERAL = "general"  # 通用应用
    UNKNOWN = "unknown"  # 未知类型


class CloudServiceType(Enum):
    """
    云服务类型分类（基于腾讯云/阿里云产品）
    """
    # 计算服务
    CVM = "cvm"  # 云服务器（CVM/ECS）

    # 数据库服务
    MYSQL = "mysql"  # MySQL 数据库
    POSTGRESQL = "postgresql"  # PostgreSQL 数据库
    MONGODB = "mongodb"  # MongoDB 数据库
    REDIS = "redis"  # Redis 缓存
    ELASTICSEARCH = "elasticsearch"  # Elasticsearch 搜索

    # 存储服务
    OBJECT_STORAGE = "object_storage"  # 对象存储（COS/OSS）
    FILE_STORAGE = "file_storage"  # 文件存储（CFS/NAS）

    # 网络服务
    LOAD_BALANCER = "load_balancer"  # 负载均衡（CLB/SLB）
    CDN = "cdn"  # CDN 加速
    VPC = "vpc"  # 私有网络

    # 容器服务
    KUBERNETES = "kubernetes"  # 容器服务（TKE/ACK）
    DOCKER = "docker"  # Docker 容器

    # 消息队列
    MESSAGE_QUEUE = "message_queue"  # 消息队列（CMQ/RocketMQ）
    KAFKA = "kafka"  # Kafka

    # AI 服务
    GPU_COMPUTE = "gpu_compute"  # GPU 云服务器
    AI_PLATFORM = "ai_platform"  # AI 平台服务

    # 大数据服务
    DATA_WAREHOUSE = "data_warehouse"  # 数据仓库
    SPARK_CLUSTER = "spark_cluster"  # Spark 集群

    # Serverless 服务
    FUNCTION_COMPUTE = "function_compute"  # 函数计算（SCF/FC）

    # 监控服务
    MONITORING = "monitoring"  # 监控告警


@dataclass
class ServiceRequirement:
    """单个云服务需求"""
    service_type: CloudServiceType
    required: bool = True  # 是否必需
    reason: str = ""  # 为什么需要这个服务
    config: Dict[str, Any] = field(default_factory=dict)  # 服务配置参数

    # 资源规格字段
    cpu_cores: Optional[int] = None
    memory_gb: Optional[int] = None
    disk_gb: Optional[int] = None
    gpu_required: bool = False
    gpu_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "service_type": self.service_type.value,
            "required": self.required,
            "reason": self.reason,
            "config": self.config
        }
        # Add resource specs if present
        if self.cpu_cores:
            result["cpu_cores"] = self.cpu_cores
        if self.memory_gb:
            result["memory_gb"] = self.memory_gb
        if self.disk_gb:
            result["disk_gb"] = self.disk_gb
        if self.gpu_required:
            result["gpu_required"] = self.gpu_required
            result["gpu_type"] = self.gpu_type
        return result


@dataclass
class CloudServiceRequirement:
    """
    云服务需求完整规格

    分析结果包含：
    1. 项目类型分类
    2. 所需云服务列表
    3. 每个服务的配置参数
    """
    # 项目信息
    project_type: ProjectType
    project_subtype: Optional[str] = None  # 项目子类型（更详细的分类）
    primary_language: Optional[str] = None  # 主要编程语言

    # 所需服务列表
    required_services: List[ServiceRequirement] = field(default_factory=list)

    # CVM 配置（如果需要）
    cvm_config: Optional[Dict[str, Any]] = None

    # 数据库配置（如果需要）
    database_config: Optional[Dict[str, Any]] = None

    # 分析元数据
    confidence: float = 0.5  # 分析置信度 (0.0-1.0)
    analysis_reasoning: str = ""  # 分析推理过程
    detected_features: List[str] = field(default_factory=list)  # 检测到的特征

    # 估算
    estimated_monthly_cost_cny: Optional[float] = None  # 预估月成本（人民币）

    def get_service_types(self) -> List[CloudServiceType]:
        """获取所有需要的服务类型"""
        return [svc.service_type for svc in self.required_services if svc.required]

    def requires_service(self, service_type: CloudServiceType) -> bool:
        """检查是否需要某个服务"""
        return service_type in self.get_service_types()

    def get_service_config(self, service_type: CloudServiceType) -> Optional[Dict[str, Any]]:
        """获取某个服务的配置"""
        for svc in self.required_services:
            if svc.service_type == service_type:
                return svc.config
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_type": self.project_type.value,
            "project_subtype": self.project_subtype,
            "required_services": [svc.to_dict() for svc in self.required_services],
            "cvm_config": self.cvm_config,
            "database_config": self.database_config,
            "confidence": self.confidence,
            "analysis_reasoning": self.analysis_reasoning,
            "detected_features": self.detected_features,
            "estimated_monthly_cost_cny": self.estimated_monthly_cost_cny
        }

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_tencent_spec(self, region: str = "ap-guangzhou") -> Dict[str, Any]:
        """
        转换为腾讯云 provider 规格格式

        Args:
            region: 腾讯云地区

        Returns:
            符合 tencent.py ResourceSpec 格式的字典
        """
        spec = {
            "region": region,
            "cvm": None,
            "mysql": None
        }

        # 查找 CVM 服务
        for svc in self.required_services:
            if svc.service_type == CloudServiceType.CVM:
                # Ensure disk_gb is at least 50GB (Tencent Cloud minimum requirement)
                disk_gb = svc.disk_gb or 100
                disk_gb = max(disk_gb, 50)

                spec["cvm"] = {
                    "cpu_cores": svc.cpu_cores or 2,
                    "memory_gb": svc.memory_gb or 4,
                    "disk_gb": disk_gb,
                    "gpu_type": svc.gpu_type if svc.gpu_required else None
                }
                break

        # 查找 MySQL 服务
        for svc in self.required_services:
            if svc.service_type == CloudServiceType.MYSQL:
                spec["mysql"] = {
                    "cpu_cores": svc.cpu_cores or 2,
                    "memory_mb": (svc.memory_gb or 4) * 1000,  # Convert GB to MB
                    "storage_gb": svc.disk_gb or 100,
                    "version": "8.0"
                }
                break

        return spec

    def get_recommended_docker_image(self) -> Dict[str, Any]:
        """
        获取推荐的 Docker 镜像信息

        Returns:
            镜像信息字典，包含 image, description, includes
        """
        from .docker_images import get_recommended_image

        # 检查是否需要 GPU
        gpu_required = False
        for svc in self.required_services:
            if svc.service_type == CloudServiceType.CVM and svc.gpu_required:
                gpu_required = True
                break

        return get_recommended_image(self.project_type, gpu_required, self.primary_language)

    def get_dockerfile(self) -> str:
        """
        生成推荐的 Dockerfile

        Returns:
            完整的 Dockerfile 内容
        """
        from .docker_images import get_dockerfile_for_project

        # 检查是否需要 GPU
        gpu_required = False
        for svc in self.required_services:
            if svc.service_type == CloudServiceType.CVM and svc.gpu_required:
                gpu_required = True
                break

        return get_dockerfile_for_project(self.project_type, gpu_required)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloudServiceRequirement':
        """从字典创建"""
        # 转换服务类型枚举
        project_type = ProjectType(data['project_type'])

        # 转换服务需求列表
        required_services = []
        for svc_data in data.get('required_services', []):
            service_type = CloudServiceType(svc_data['service_type'])
            required_services.append(ServiceRequirement(
                service_type=service_type,
                required=svc_data.get('required', True),
                reason=svc_data.get('reason', ''),
                config=svc_data.get('config', {})
            ))

        return cls(
            project_type=project_type,
            project_subtype=data.get('project_subtype'),
            required_services=required_services,
            cvm_config=data.get('cvm_config'),
            database_config=data.get('database_config'),
            confidence=data.get('confidence', 0.5),
            analysis_reasoning=data.get('analysis_reasoning', ''),
            detected_features=data.get('detected_features', []),
            estimated_monthly_cost_cny=data.get('estimated_monthly_cost_cny')
        )

    def get_summary(self) -> str:
        """获取可读摘要"""
        lines = [
            f"项目类型: {self.project_type.value}",
        ]

        if self.project_subtype:
            lines.append(f"子类型: {self.project_subtype}")

        lines.append(f"置信度: {self.confidence:.1%}")
        lines.append(f"\n需要的云服务:")

        for svc in self.required_services:
            status = "✓ 必需" if svc.required else "○ 可选"
            lines.append(f"  {status} {svc.service_type.value}")
            if svc.reason:
                lines.append(f"     原因: {svc.reason}")

        if self.estimated_monthly_cost_cny:
            lines.append(f"\n预估月成本: ¥{self.estimated_monthly_cost_cny:.2f}")

        return "\n".join(lines)


# 项目类型到服务映射模板
PROJECT_SERVICE_MAPPING = {
    ProjectType.WEB_FRONTEND: [
        CloudServiceType.CVM,
        CloudServiceType.CDN,
    ],

    ProjectType.WEB_BACKEND: [
        CloudServiceType.CVM,
        CloudServiceType.MYSQL,
        CloudServiceType.REDIS,
        CloudServiceType.LOAD_BALANCER,
    ],

    ProjectType.WEB_FULLSTACK: [
        CloudServiceType.CVM,
        CloudServiceType.MYSQL,
        CloudServiceType.REDIS,
        CloudServiceType.OBJECT_STORAGE,
        CloudServiceType.CDN,
    ],

    ProjectType.DATABASE_APP: [
        CloudServiceType.CVM,
        CloudServiceType.MYSQL,
    ],

    ProjectType.MICROSERVICES: [
        CloudServiceType.CVM,
        CloudServiceType.KUBERNETES,
        CloudServiceType.MYSQL,
        CloudServiceType.REDIS,
        CloudServiceType.MESSAGE_QUEUE,
        CloudServiceType.LOAD_BALANCER,
    ],

    ProjectType.ML_TRAINING: [
        CloudServiceType.GPU_COMPUTE,
        CloudServiceType.OBJECT_STORAGE,
    ],

    ProjectType.ML_INFERENCE: [
        CloudServiceType.CVM,
        CloudServiceType.REDIS,
    ],

    ProjectType.LLM_SERVICE: [
        CloudServiceType.GPU_COMPUTE,
        CloudServiceType.REDIS,
        CloudServiceType.LOAD_BALANCER,
    ],

    ProjectType.DATA_ETL: [
        CloudServiceType.CVM,
        CloudServiceType.MYSQL,
        CloudServiceType.OBJECT_STORAGE,
    ],

    ProjectType.BIG_DATA: [
        CloudServiceType.CVM,
        CloudServiceType.SPARK_CLUSTER,
        CloudServiceType.DATA_WAREHOUSE,
        CloudServiceType.OBJECT_STORAGE,
    ],

    ProjectType.MOBILE_BACKEND: [
        CloudServiceType.CVM,
        CloudServiceType.MYSQL,
        CloudServiceType.REDIS,
        CloudServiceType.OBJECT_STORAGE,
        CloudServiceType.CDN,
    ],

    ProjectType.ECOMMERCE: [
        CloudServiceType.CVM,
        CloudServiceType.MYSQL,
        CloudServiceType.REDIS,
        CloudServiceType.OBJECT_STORAGE,
        CloudServiceType.CDN,
        CloudServiceType.LOAD_BALANCER,
    ],
}


def get_default_services_for_project(project_type: ProjectType) -> List[CloudServiceType]:
    """获取项目类型的默认服务列表"""
    return PROJECT_SERVICE_MAPPING.get(project_type, [CloudServiceType.CVM])
