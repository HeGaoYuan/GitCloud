#!/usr/bin/env python3
"""
Resource Specification Module for GitCloud
-------------------------------------------
Defines standardized resource specifications for cloud and on-premises deployments.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json


@dataclass
class ResourceSpec:
    """
    Standardized resource specification for GitCloud deployments.

    This data structure is used across all providers (Tencent, Alibaba, On-premises)
    to specify resource requirements.
    """

    # Compute resources
    cpu_cores: int  # Number of CPU cores
    memory_gb: int  # Memory in GB
    disk_gb: int = 50  # Disk space in GB (default 50GB)

    # GPU resources (optional)
    gpu_required: bool = False
    gpu_type: Optional[str] = None  # e.g., "T4", "V100", "A10", "A100"
    gpu_count: int = 1  # Number of GPUs
    gpu_memory_gb: Optional[int] = None  # GPU memory in GB

    # Network resources
    bandwidth_mbps: int = 100  # Network bandwidth in Mbps

    # Analysis metadata
    analysis_reasoning: Optional[str] = None  # Why these resources were chosen
    project_type: Optional[str] = None  # e.g., "web", "ml", "api", "data_processing"
    confidence: Optional[float] = None  # Confidence level (0.0-1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceSpec':
        """Create ResourceSpec from dictionary"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'ResourceSpec':
        """Create ResourceSpec from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate resource specification

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.cpu_cores < 1:
            return False, "CPU cores must be at least 1"

        if self.memory_gb < 1:
            return False, "Memory must be at least 1GB"

        if self.disk_gb < 10:
            return False, "Disk space must be at least 10GB"

        if self.gpu_required and not self.gpu_type:
            return False, "GPU type must be specified when GPU is required"

        if self.gpu_count < 1:
            return False, "GPU count must be at least 1"

        if self.bandwidth_mbps < 1:
            return False, "Bandwidth must be at least 1 Mbps"

        return True, None

    def get_summary(self) -> str:
        """Get human-readable summary of resource spec"""
        lines = [
            f"CPU: {self.cpu_cores} cores",
            f"Memory: {self.memory_gb} GB",
            f"Disk: {self.disk_gb} GB",
        ]

        if self.gpu_required and self.gpu_type:
            gpu_str = f"GPU: {self.gpu_count}x {self.gpu_type}"
            if self.gpu_memory_gb:
                gpu_str += f" ({self.gpu_memory_gb}GB VRAM)"
            lines.append(gpu_str)
        else:
            lines.append("GPU: None")

        lines.append(f"Bandwidth: {self.bandwidth_mbps} Mbps")

        if self.project_type:
            lines.append(f"Project Type: {self.project_type}")

        if self.confidence:
            lines.append(f"Confidence: {self.confidence:.1%}")

        return "\n".join(lines)


# Predefined resource templates for common scenarios
RESOURCE_TEMPLATES = {
    "minimal": ResourceSpec(
        cpu_cores=2,
        memory_gb=4,
        disk_gb=50,
        bandwidth_mbps=50,
        project_type="minimal",
        analysis_reasoning="Minimal resources for simple applications"
    ),

    "small_web": ResourceSpec(
        cpu_cores=2,
        memory_gb=4,
        disk_gb=50,
        bandwidth_mbps=100,
        project_type="web",
        analysis_reasoning="Small web service or API"
    ),

    "medium_web": ResourceSpec(
        cpu_cores=4,
        memory_gb=8,
        disk_gb=100,
        bandwidth_mbps=200,
        project_type="web",
        analysis_reasoning="Medium web service with moderate traffic"
    ),

    "large_web": ResourceSpec(
        cpu_cores=8,
        memory_gb=16,
        disk_gb=200,
        bandwidth_mbps=500,
        project_type="web",
        analysis_reasoning="Large web service with high traffic"
    ),

    "ml_small": ResourceSpec(
        cpu_cores=8,
        memory_gb=32,
        disk_gb=200,
        gpu_required=True,
        gpu_type="T4",
        gpu_count=1,
        gpu_memory_gb=16,
        bandwidth_mbps=200,
        project_type="ml",
        analysis_reasoning="Small ML training or inference"
    ),

    "ml_medium": ResourceSpec(
        cpu_cores=16,
        memory_gb=64,
        disk_gb=500,
        gpu_required=True,
        gpu_type="V100",
        gpu_count=1,
        gpu_memory_gb=32,
        bandwidth_mbps=500,
        project_type="ml",
        analysis_reasoning="Medium ML training with moderate model size"
    ),

    "ml_large": ResourceSpec(
        cpu_cores=32,
        memory_gb=128,
        disk_gb=1000,
        gpu_required=True,
        gpu_type="A100",
        gpu_count=1,
        gpu_memory_gb=80,
        bandwidth_mbps=1000,
        project_type="ml",
        analysis_reasoning="Large ML training or LLM inference"
    ),

    "data_processing": ResourceSpec(
        cpu_cores=16,
        memory_gb=64,
        disk_gb=500,
        bandwidth_mbps=500,
        project_type="data_processing",
        analysis_reasoning="Data processing and ETL workloads"
    ),
}


def get_template(template_name: str) -> Optional[ResourceSpec]:
    """Get predefined resource template by name"""
    return RESOURCE_TEMPLATES.get(template_name)


def list_templates() -> Dict[str, ResourceSpec]:
    """List all available resource templates"""
    return RESOURCE_TEMPLATES.copy()
