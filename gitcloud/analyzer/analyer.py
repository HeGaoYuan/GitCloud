#!/usr/bin/env python3
"""
Enhanced Resource Analyzer Agent for GitCloud
----------------------------------------------
Intelligently analyzes GitHub repositories to determine:
1. Project type classification (comprehensive software domain taxonomy)
2. Required cloud services (based on Tencent/Alibaba cloud products)
3. Resource specifications for each service
"""

import os
import re
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

from .cloud_service_spec import (
    CloudServiceRequirement,
    ServiceRequirement,
    ProjectType,
    CloudServiceType,
    get_default_services_for_project
)
from .resource_spec import ResourceSpec
from .github_fetcher import GitHubFetcher


# ANSI color codes for log output
class LogColors:
    INFO = '\033[96m'      # Cyan
    SUCCESS = '\033[1;32m' # Bold Green
    DEBUG = '\033[2;37m'   # Dim White
    RESET = '\033[0m'


class EnhancedResourceAnalyzer:
    """Enhanced analyzer for project type and cloud service requirements"""

    def __init__(self, repo_url: str, verbose: bool = False, model: str = 'deepseek', session_dir=None, use_api: bool = True):
        self.repo_url = repo_url
        self.verbose = verbose
        self.model = model
        self.session_dir = session_dir
        self.use_api = use_api  # Use GitHub API instead of cloning
        self.analysis_data = {}

    def log(self, message: str):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[ResourceAnalyzer] {message}")

    def analyze(self) -> CloudServiceRequirement:
        """
        Perform complete analysis and return cloud service requirements

        Returns:
            CloudServiceRequirement object with project type and required services
        """
        if self.use_api:
            print(f"{LogColors.INFO}  🔍 Fetching repository files via GitHub API...{LogColors.RESET}")
        else:
            print(f"{LogColors.INFO}  🔍 Cloning and analyzing repository...{LogColors.RESET}")
        print(f"{LogColors.DEBUG}     Repository: {self.repo_url}{LogColors.RESET}")

        # Step 1: Get repository files (via API or clone)
        temp_dir = None
        if self.use_api:
            temp_dir = self._fetch_via_api()
        else:
            temp_dir = self._clone_repository()

        if not temp_dir:
            print(f"{LogColors.DEBUG}  ⚠️  Failed to access repository, using default configuration{LogColors.RESET}")
            return self._create_default_requirement()

        try:
            # Step 2: Analyze repository structure
            self._analyze_repository_files(temp_dir)

            # Step 3: Read README
            readme_content = self._read_readme(temp_dir)
            if readme_content:
                self.analysis_data['readme'] = readme_content[:5000]

            # Step 4: Read key files for AI analysis
            self._read_key_files(temp_dir)

            # Step 5: Try AI analysis first (if available)
            print(f"{LogColors.INFO}  🤖 Attempting AI-powered analysis...{LogColors.RESET}")
            ai_requirement = self._ai_analyze_comprehensive(temp_dir)

            if ai_requirement:
                print(f"{LogColors.SUCCESS}  ✅ AI analysis successful{LogColors.RESET}")
                return ai_requirement

            # Step 6: Fallback to rule-based analysis
            print(f"{LogColors.INFO}  ⚙️  Using rule-based analysis...{LogColors.RESET}")

            # Detect project type (comprehensive classification)
            project_type, subtype, features = self._detect_project_type_comprehensive(temp_dir)
            self.analysis_data['project_type'] = project_type
            self.analysis_data['subtype'] = subtype
            self.analysis_data['features'] = features

            # Determine required cloud services
            required_services = self._determine_cloud_services(project_type, features, temp_dir)

            # Generate CVM and database configurations
            cvm_config, db_config = self._generate_service_configs(project_type, features)

            # Detect primary language
            primary_language = self._detect_primary_language()

            # Calculate confidence
            confidence = self._calculate_confidence(features)

            # Create requirement object
            requirement = CloudServiceRequirement(
                project_type=project_type,
                project_subtype=subtype,
                primary_language=primary_language,
                required_services=required_services,
                cvm_config=cvm_config,
                database_config=db_config,
                confidence=confidence,
                analysis_reasoning=self._build_reasoning(project_type, features),
                detected_features=features
            )

            print(f"\n{LogColors.SUCCESS}  ✅ Analysis completed{LogColors.RESET}")
            print(f"{LogColors.DEBUG}     Project Type: {project_type.value}{LogColors.RESET}")
            if subtype:
                print(f"{LogColors.DEBUG}     Subtype: {subtype}{LogColors.RESET}")
            print(f"{LogColors.DEBUG}     Confidence: {confidence:.1%}{LogColors.RESET}")
            print(f"{LogColors.DEBUG}     Required Services: {len(required_services)}{LogColors.RESET}")

            return requirement

        finally:
            # Cleanup
            self.log(f"Keeping temp dir for debugging: {temp_dir}")

    def _fetch_via_api(self) -> Optional[str]:
        """
        Fetch repository files via GitHub API instead of cloning

        Returns:
            Path to directory containing fetched files, or None on failure
        """
        try:
            # Use session directory if provided, otherwise use temp directory
            if self.session_dir:
                temp_dir = str(Path(self.session_dir) / "repo_api_fetch")
                Path(temp_dir).mkdir(parents=True, exist_ok=True)
            else:
                temp_dir = tempfile.mkdtemp(prefix="gitcloud_api_")
            self.log(f"Fetching files to {temp_dir}")

            # Create GitHub fetcher
            fetcher = GitHubFetcher(self.repo_url, verbose=self.verbose)

            # Fetch all analysis files
            fetched_files = fetcher.fetch_analysis_files(output_dir=temp_dir)

            if len(fetched_files) > 0:
                self.log(f"Successfully fetched {len(fetched_files)} files via API")
                print(f"{LogColors.SUCCESS}  ✅ Fetched {len(fetched_files)} files via GitHub API{LogColors.RESET}")
                return temp_dir
            else:
                self.log("No files fetched via API, falling back to clone")
                print(f"{LogColors.DEBUG}  ⚠️  API fetch returned no files, trying clone...{LogColors.RESET}")
                return self._clone_repository()

        except Exception as e:
            self.log(f"Error fetching via API: {e}, falling back to clone")
            print(f"{LogColors.DEBUG}  ⚠️  API fetch failed, trying clone...{LogColors.RESET}")
            return self._clone_repository()

    def _clone_repository(self) -> Optional[str]:
        """Clone repository to temporary directory"""
        try:
            # Use session directory if provided, otherwise use temp directory
            if self.session_dir:
                temp_dir = str(Path(self.session_dir) / "repo_clone")
                Path(temp_dir).mkdir(parents=True, exist_ok=True)
            else:
                temp_dir = tempfile.mkdtemp(prefix="gitcloud_analysis_")
            self.log(f"Cloning repository to {temp_dir}")

            result = subprocess.run(
                ["git", "clone", "--depth", "1", self.repo_url, temp_dir],
                capture_output=True,
                timeout=60,
                text=True
            )

            if result.returncode == 0:
                self.log("Repository cloned successfully")
                print(f"{LogColors.SUCCESS}  ✅ Repository cloned successfully{LogColors.RESET}")
                return temp_dir
            else:
                self.log(f"Failed to clone: {result.stderr}")
                return None

        except Exception as e:
            self.log(f"Error cloning repository: {e}")
            return None

    def _analyze_repository_files(self, repo_path: str):
        """Analyze repository file structure with comprehensive detection"""
        self.log("Analyzing repository files")

        # 扩展的文件模式检测
        file_patterns = {
            # Python
            'requirements.txt': 'python_deps',
            'setup.py': 'python_setup',
            'pyproject.toml': 'python_modern',
            'Pipfile': 'python_pipenv',
            'conda.yml': 'python_conda',
            'environment.yml': 'python_conda',

            # Node.js
            'package.json': 'nodejs',
            'yarn.lock': 'nodejs_yarn',
            'pnpm-lock.yaml': 'nodejs_pnpm',

            # Java
            'pom.xml': 'java_maven',
            'build.gradle': 'java_gradle',
            'build.gradle.kts': 'java_gradle_kotlin',

            # Go
            'go.mod': 'golang',
            'go.sum': 'golang',

            # Rust
            'Cargo.toml': 'rust',

            # PHP
            'composer.json': 'php',

            # Ruby
            'Gemfile': 'ruby',

            # .NET
            '*.csproj': 'dotnet',
            '*.sln': 'dotnet_solution',

            # 容器化
            'Dockerfile': 'docker',
            'docker-compose.yml': 'docker_compose',
            'docker-compose.yaml': 'docker_compose',

            # Kubernetes
            '*.yaml': 'k8s_config',
            'helm': 'helm',

            # 数据库
            '*.sql': 'sql_files',
            'migrations': 'db_migrations',

            # ML/AI
            '*.ipynb': 'jupyter',
            'train.py': 'ml_training',
            'model.py': 'ml_model',
            'inference.py': 'ml_inference',
            'requirements-ml.txt': 'ml_requirements',

            # 前端框架
            'angular.json': 'angular',
            'vue.config.js': 'vue',
            'next.config.js': 'nextjs',
            'nuxt.config.js': 'nuxtjs',
            'gatsby-config.js': 'gatsby',
            'svelte.config.js': 'svelte',

            # 移动端
            'android': 'android',
            'ios': 'ios',
            'pubspec.yaml': 'flutter',
            'capacitor.config.json': 'capacitor',

            # CI/CD
            '.github/workflows': 'github_actions',
            '.gitlab-ci.yml': 'gitlab_ci',
            'Jenkinsfile': 'jenkins',

            # 配置
            'terraform': 'terraform',
            'ansible': 'ansible',
        }

        found_files = []
        repo_path_obj = Path(repo_path)

        for pattern, file_type in file_patterns.items():
            if '*' in pattern or pattern in ['migrations', 'android', 'ios', 'helm', 'terraform', 'ansible']:
                # Directory or glob pattern
                matches = list(repo_path_obj.rglob(pattern))
            else:
                # Exact filename
                matches = list(repo_path_obj.rglob(pattern))

            if matches:
                found_files.append(file_type)
                self.log(f"Found {file_type}: {len(matches)} items")

        self.analysis_data['found_files'] = found_files

        # Count files
        try:
            file_count = sum(1 for _ in repo_path_obj.rglob('*') if _.is_file())
            self.analysis_data['file_count'] = file_count
        except Exception:
            pass

    def _read_readme(self, repo_path: str) -> Optional[str]:
        """Read README file"""
        readme_names = ['README.md', 'README.rst', 'README.txt', 'README', 'readme.md']

        for readme_name in readme_names:
            readme_path = Path(repo_path) / readme_name
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        self.log(f"Read README: {len(content)} characters")
                        return content
                except Exception as e:
                    self.log(f"Error reading README: {e}")

        return None

    def _read_key_files(self, repo_path: str):
        """Read key configuration files for AI analysis"""
        key_files = {
            'requirements.txt': 'python_deps',
            'package.json': 'node_deps',
            'go.mod': 'go_deps',
            'pom.xml': 'java_deps',
            'Cargo.toml': 'rust_deps',
            'Dockerfile': 'docker',
            'docker-compose.yml': 'docker_compose',
            '.env.example': 'env_example',
            'requirements-dev.txt': 'dev_deps'
        }

        for filename, key in key_files.items():
            file_path = Path(repo_path) / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        self.analysis_data[key] = content[:3000]  # Limit to 3000 chars
                        self.log(f"Read {filename}: {len(content)} characters")
                except Exception as e:
                    self.log(f"Error reading {filename}: {e}")

    def _ai_analyze_comprehensive(self, repo_path: str) -> Optional[CloudServiceRequirement]:
        """
        Use AI (Anthropic Claude) to analyze project and determine requirements

        Returns:
            CloudServiceRequirement if AI analysis succeeds, None otherwise
        """
        try:
            import anthropic
        except ImportError:
            self.log("Anthropic package not installed, skipping AI analysis")
            return None

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            self.log("ANTHROPIC_API_KEY not set, skipping AI analysis")
            return None

        try:
            # Prepare analysis context
            context_parts = []

            # Add README
            if 'readme' in self.analysis_data:
                context_parts.append(f"README内容:\n{self.analysis_data['readme']}")

            # Add dependencies
            if 'python_deps' in self.analysis_data:
                context_parts.append(f"\nrequirements.txt:\n{self.analysis_data['python_deps']}")
            if 'node_deps' in self.analysis_data:
                context_parts.append(f"\npackage.json:\n{self.analysis_data['node_deps']}")
            if 'go_deps' in self.analysis_data:
                context_parts.append(f"\ngo.mod:\n{self.analysis_data['go_deps']}")

            # Add Docker files
            if 'docker' in self.analysis_data:
                context_parts.append(f"\nDockerfile:\n{self.analysis_data['docker']}")
            if 'docker_compose' in self.analysis_data:
                context_parts.append(f"\ndocker-compose.yml:\n{self.analysis_data['docker_compose']}")

            # Add found files summary
            if 'found_files' in self.analysis_data:
                context_parts.append(f"\n检测到的文件类型: {', '.join(self.analysis_data['found_files'])}")

            context = "\n".join(context_parts)

            # Project type options
            project_types = [t.value for t in ProjectType]

            # Construct AI prompt
            prompt = f"""你是一个云资源分析专家。请分析以下GitHub项目，判断项目类型和所需云服务资源。

项目信息:
{context}

请分析并返回JSON格式结果（仅返回JSON，不要其他文字）:
{{
  "project_type": "选择一个: {', '.join(project_types)}",
  "project_subtype": "项目子类型描述（可选）",
  "primary_language": "主要编程语言（golang/python/nodejs/java/rust等）",
  "needs_gpu": true/false,
  "gpu_type": "T4/V100/A10/A100/none",
  "cpu_cores": 数字,
  "memory_gb": 数字,
  "disk_gb": 数字,
  "needs_mysql": true/false,
  "needs_redis": true/false,
  "needs_object_storage": true/false,
  "needs_cdn": true/false,
  "reasoning": "分析原因"
}}

注意：
- project_type 必须从上述列表中选择
- primary_language 要根据检测到的依赖文件和代码判断
- GPU类型用于机器学习项目：T4(入门)、V100(中端)、A10(高端)、A100(顶级)
- CPU/内存/磁盘要根据项目规模合理估算
- 数据库、缓存等根据项目实际需求判断"""

            # Call AI API based on selected model
            if self.model == 'deepseek':
                client = anthropic.Anthropic(api_key=api_key, base_url="https://api.deepseek.com/anthropic")
                model_name = "deepseek-chat"
            else:  # anthropic
                client = anthropic.Anthropic(api_key=api_key)
                model_name = "claude-sonnet-4-20250514"

            message = client.messages.create(
                model=model_name,
                max_tokens=1000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON
            result = json.loads(response_text)

            # Validate and construct CloudServiceRequirement
            project_type_str = result.get('project_type', 'WEB_APPLICATION')
            try:
                project_type = ProjectType(project_type_str)
            except ValueError:
                # Try to match by value
                project_type = ProjectType.WEB_APPLICATION
                for pt in ProjectType:
                    if pt.value == project_type_str:
                        project_type = pt
                        break

            # Build required services list
            required_services = []

            # CVM config
            cvm_config = ServiceRequirement(
                service_type=CloudServiceType.CVM,
                cpu_cores=result.get('cpu_cores', 2),
                memory_gb=result.get('memory_gb', 4),
                disk_gb=max(result.get('disk_gb', 100), 50),  # Ensure minimum 50GB
                gpu_required=result.get('needs_gpu', False),
                gpu_type=result.get('gpu_type') if result.get('needs_gpu') else None
            )
            required_services.append(cvm_config)

            # MySQL
            if result.get('needs_mysql', False):
                mysql_config = ServiceRequirement(
                    service_type=CloudServiceType.MYSQL,
                    cpu_cores=2,
                    memory_gb=4,
                    disk_gb=100
                )
                required_services.append(mysql_config)

            # Redis
            if result.get('needs_redis', False):
                redis_config = ServiceRequirement(
                    service_type=CloudServiceType.REDIS,
                    memory_gb=2
                )
                required_services.append(redis_config)

            # Object Storage
            if result.get('needs_object_storage', False):
                storage_config = ServiceRequirement(
                    service_type=CloudServiceType.OBJECT_STORAGE,
                    disk_gb=500
                )
                required_services.append(storage_config)

            # CDN
            if result.get('needs_cdn', False):
                cdn_config = ServiceRequirement(
                    service_type=CloudServiceType.CDN
                )
                required_services.append(cdn_config)

            # Create requirement object
            requirement = CloudServiceRequirement(
                project_type=project_type,
                project_subtype=result.get('project_subtype'),
                primary_language=result.get('primary_language'),
                required_services=required_services,
                analysis_reasoning=result.get('reasoning', 'AI分析'),
                confidence=0.9  # High confidence for AI analysis
            )

            return requirement

        except Exception as e:
            self.log(f"AI analysis failed: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()
            return None

    def _detect_project_type_comprehensive(self, repo_path: str) -> Tuple[ProjectType, Optional[str], List[str]]:
        """
        Comprehensive project type detection with subtype classification

        Returns:
            Tuple of (ProjectType, subtype, detected_features)
        """
        found_files = self.analysis_data.get('found_files', [])
        readme = self.analysis_data.get('readme', '').lower()
        features = []

        # === ML/AI 项目检测 ===
        ml_indicators = ['ml_training', 'ml_model', 'ml_inference', 'jupyter', 'ml_requirements']
        if any(ind in found_files for ind in ml_indicators):
            features.append('machine_learning')

            # Check for LLM-specific keywords
            llm_keywords = ['llm', 'gpt', 'bert', 'transformer', 'huggingface', 'openai', 'chatgpt']
            if any(kw in readme for kw in llm_keywords):
                features.append('large_language_model')
                return ProjectType.LLM_SERVICE, 'LLM推理服务', features

            # Check for training vs inference
            if 'ml_training' in found_files or 'train' in readme:
                features.append('training')
                return ProjectType.ML_TRAINING, 'ML模型训练', features
            else:
                features.append('inference')
                return ProjectType.ML_INFERENCE, 'ML模型推理', features

        # Check Python ML dependencies
        if 'python_deps' in found_files:
            req_path = Path(repo_path) / 'requirements.txt'
            if req_path.exists():
                try:
                    content = req_path.read_text().lower()
                    ml_packages = ['tensorflow', 'torch', 'pytorch', 'keras', 'sklearn',
                                   'transformers', 'numpy', 'pandas', 'scipy', 'jax']
                    if any(pkg in content for pkg in ml_packages):
                        features.append('machine_learning')
                        return ProjectType.ML_INFERENCE, 'Python ML应用', features
                except Exception:
                    pass

        # === 数据处理项目检测 ===
        data_keywords = ['spark', 'hadoop', 'airflow', 'luigi', 'dask', 'flink', 'kafka']
        if any(kw in readme for kw in data_keywords):
            features.append('big_data')
            if 'spark' in readme or 'hadoop' in readme:
                return ProjectType.BIG_DATA, 'Spark/Hadoop大数据', features
            elif 'kafka' in readme or 'flink' in readme:
                return ProjectType.STREAM_PROCESSING, '流处理', features
            else:
                return ProjectType.DATA_ETL, 'ETL数据处理', features

        # === 前端项目检测 ===
        frontend_frameworks = ['angular', 'vue', 'nextjs', 'nuxtjs', 'gatsby', 'svelte']
        if any(fw in found_files for fw in frontend_frameworks):
            features.append('frontend_framework')
            return ProjectType.WEB_FRONTEND, '前端应用', features

        # Check for static site
        if 'nodejs' in found_files and 'package.json' in Path(repo_path).rglob('*'):
            try:
                pkg_json = Path(repo_path) / 'package.json'
                if pkg_json.exists():
                    pkg_content = pkg_json.read_text()
                    if 'gatsby' in pkg_content or 'next' in pkg_content or 'vite' in pkg_content:
                        features.append('static_site')
                        return ProjectType.WEB_STATIC, '静态网站', features
            except:
                pass

        # === 后端 API 检测 ===
        # Check for API frameworks
        api_indicators = {
            'flask': 'Flask API',
            'fastapi': 'FastAPI',
            'django': 'Django',
            'express': 'Express.js',
            'koa': 'Koa.js',
            'spring': 'Spring Boot',
            'gin': 'Gin (Go)',
            'echo': 'Echo (Go)',
            'actix': 'Actix (Rust)',
        }

        for framework, description in api_indicators.items():
            if framework in readme or framework in str(found_files):
                features.append('backend_api')
                features.append(framework)
                return ProjectType.WEB_BACKEND, description, features

        # === 微服务检测 ===
        if 'k8s_config' in found_files or 'helm' in found_files or 'docker_compose' in found_files:
            microservice_keywords = ['microservice', 'grpc', 'service mesh', 'istio']
            if any(kw in readme for kw in microservice_keywords):
                features.append('microservices')
                return ProjectType.MICROSERVICES, '微服务架构', features

        # === 全栈项目检测 ===
        has_frontend = any(fw in found_files for fw in ['angular', 'vue', 'nodejs'])
        has_backend = 'python_deps' in found_files or 'java_maven' in found_files
        if has_frontend and has_backend:
            features.append('fullstack')
            return ProjectType.WEB_FULLSTACK, '全栈应用', features

        # === 移动后端检测 ===
        mobile_keywords = ['mobile', 'ios', 'android', 'flutter', 'react native']
        if any(kw in readme for kw in mobile_keywords):
            features.append('mobile_backend')
            return ProjectType.MOBILE_BACKEND, '移动应用后端', features

        # === 电商项目检测 ===
        ecommerce_keywords = ['ecommerce', 'e-commerce', 'shopping', 'cart', 'payment', 'order']
        if any(kw in readme for kw in ecommerce_keywords):
            features.append('ecommerce')
            return ProjectType.ECOMMERCE, '电商平台', features

        # === 游戏服务器检测 ===
        game_keywords = ['game', 'unity', 'unreal', 'multiplayer', 'mmo']
        if any(kw in readme for kw in game_keywords):
            features.append('game_server')
            return ProjectType.GAME_SERVER, '游戏服务器', features

        # === CMS 检测 ===
        cms_keywords = ['cms', 'content management', 'wordpress', 'strapi', 'ghost']
        if any(kw in readme for kw in cms_keywords):
            features.append('cms')
            return ProjectType.CONTENT_MANAGEMENT, 'CMS系统', features

        # === 数据库应用检测 ===
        if 'sql_files' in found_files or 'db_migrations' in found_files:
            features.append('database_heavy')
            return ProjectType.DATABASE_APP, '数据库应用', features

        # === CI/CD 工具检测 ===
        if any(ci in found_files for ci in ['github_actions', 'gitlab_ci', 'jenkins']):
            features.append('cicd')
            return ProjectType.CI_CD, 'CI/CD系统', features

        # === 默认：Web 应用或通用应用 ===
        if 'nodejs' in found_files or 'python_deps' in found_files or 'golang' in found_files:
            features.append('web_application')
            return ProjectType.WEB_BACKEND, 'Web后端应用', features

        return ProjectType.GENERAL, None, features

    def _determine_cloud_services(
        self,
        project_type: ProjectType,
        features: List[str],
        repo_path: str
    ) -> List[ServiceRequirement]:
        """
        Determine required cloud services based on project type and features
        """
        required_services = []

        # Get default services for this project type
        default_services = get_default_services_for_project(project_type)

        # CVM (云服务器) - 几乎所有项目都需要
        if CloudServiceType.CVM in default_services or project_type != ProjectType.SERVERLESS:
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.CVM,
                required=True,
                reason="运行应用程序主服务"
            ))

        # MySQL 数据库
        if self._needs_mysql(project_type, features, repo_path):
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.MYSQL,
                required=True,
                reason="持久化存储业务数据"
            ))

        # Redis 缓存
        if self._needs_redis(project_type, features):
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.REDIS,
                required=False,
                reason="缓存热点数据，提升性能"
            ))

        # 对象存储
        if self._needs_object_storage(project_type, features):
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.OBJECT_STORAGE,
                required=False,
                reason="存储文件、图片、视频等静态资源"
            ))

        # CDN
        if self._needs_cdn(project_type, features):
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.CDN,
                required=False,
                reason="加速静态资源访问"
            ))

        # 负载均衡
        if self._needs_load_balancer(project_type, features):
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.LOAD_BALANCER,
                required=False,
                reason="分发流量，提高可用性"
            ))

        # GPU 计算
        if 'machine_learning' in features or project_type in [
            ProjectType.ML_TRAINING, ProjectType.ML_INFERENCE, ProjectType.LLM_SERVICE
        ]:
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.GPU_COMPUTE,
                required=True,
                reason="GPU加速模型训练/推理"
            ))

        # Kubernetes
        if 'microservices' in features or 'k8s_config' in self.analysis_data.get('found_files', []):
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.KUBERNETES,
                required=False,
                reason="容器编排和微服务管理"
            ))

        # 消息队列
        if project_type in [ProjectType.MICROSERVICES, ProjectType.BIG_DATA, ProjectType.STREAM_PROCESSING]:
            required_services.append(ServiceRequirement(
                service_type=CloudServiceType.MESSAGE_QUEUE,
                required=False,
                reason="异步消息处理"
            ))

        return required_services

    def _needs_mysql(self, project_type: ProjectType, features: List[str], repo_path: str) -> bool:
        """判断是否需要 MySQL"""
        # 明确需要数据库的项目类型
        needs_db_types = [
            ProjectType.WEB_BACKEND,
            ProjectType.WEB_FULLSTACK,
            ProjectType.DATABASE_APP,
            ProjectType.MICROSERVICES,
            ProjectType.MOBILE_BACKEND,
            ProjectType.ECOMMERCE,
            ProjectType.CRM_ERP,
            ProjectType.CONTENT_MANAGEMENT,
        ]

        if project_type in needs_db_types:
            return True

        # 检查是否有数据库配置文件
        found_files = self.analysis_data.get('found_files', [])
        if 'sql_files' in found_files or 'db_migrations' in found_files:
            return True

        # 检查依赖中是否有数据库驱动
        if 'python_deps' in found_files:
            req_path = Path(repo_path) / 'requirements.txt'
            if req_path.exists():
                try:
                    content = req_path.read_text().lower()
                    db_packages = ['mysql', 'pymysql', 'mysqlclient', 'sqlalchemy', 'django', 'flask-sqlalchemy']
                    if any(pkg in content for pkg in db_packages):
                        return True
                except:
                    pass

        return False

    def _needs_redis(self, project_type: ProjectType, features: List[str]) -> bool:
        """判断是否需要 Redis"""
        # 高流量、需要缓存的项目类型
        return project_type in [
            ProjectType.WEB_BACKEND,
            ProjectType.WEB_FULLSTACK,
            ProjectType.MICROSERVICES,
            ProjectType.MOBILE_BACKEND,
            ProjectType.ECOMMERCE,
            ProjectType.LLM_SERVICE,
        ]

    def _needs_object_storage(self, project_type: ProjectType, features: List[str]) -> bool:
        """判断是否需要对象存储"""
        return project_type in [
            ProjectType.WEB_FULLSTACK,
            ProjectType.MOBILE_BACKEND,
            ProjectType.ECOMMERCE,
            ProjectType.CONTENT_MANAGEMENT,
            ProjectType.ML_TRAINING,
            ProjectType.DATA_ETL,
            ProjectType.BIG_DATA,
        ]

    def _needs_cdn(self, project_type: ProjectType, features: List[str]) -> bool:
        """判断是否需要 CDN"""
        return project_type in [
            ProjectType.WEB_FRONTEND,
            ProjectType.WEB_STATIC,
            ProjectType.WEB_FULLSTACK,
            ProjectType.ECOMMERCE,
            ProjectType.CONTENT_MANAGEMENT,
        ]

    def _needs_load_balancer(self, project_type: ProjectType, features: List[str]) -> bool:
        """判断是否需要负载均衡"""
        return project_type in [
            ProjectType.MICROSERVICES,
            ProjectType.ECOMMERCE,
            ProjectType.LLM_SERVICE,
        ] or 'high_traffic' in features

    def _generate_service_configs(
        self,
        project_type: ProjectType,
        features: List[str]
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Generate CVM and database configurations based on project type

        Returns:
            Tuple of (cvm_config, database_config)
        """
        cvm_config = None
        db_config = None

        # === CVM 配置 ===
        if project_type in [ProjectType.ML_TRAINING, ProjectType.ML_INFERENCE, ProjectType.LLM_SERVICE]:
            # ML/AI 项目需要 GPU
            gpu_type = 'T4' if project_type == ProjectType.ML_INFERENCE else 'V100'
            cvm_config = {
                'cpu_cores': 8 if project_type == ProjectType.ML_INFERENCE else 16,
                'memory_gb': 32 if project_type == ProjectType.ML_INFERENCE else 64,
                'disk_gb': 200 if project_type == ProjectType.ML_INFERENCE else 500,
                'gpu_type': gpu_type,
            }
        elif project_type in [ProjectType.BIG_DATA, ProjectType.DATA_ETL]:
            # 数据处理项目
            cvm_config = {
                'cpu_cores': 16,
                'memory_gb': 64,
                'disk_gb': 500,
            }
        elif project_type in [ProjectType.ECOMMERCE, ProjectType.MICROSERVICES]:
            # 高流量项目
            cvm_config = {
                'cpu_cores': 8,
                'memory_gb': 16,
                'disk_gb': 200,
            }
        else:
            # 默认配置
            cvm_config = {
                'cpu_cores': 2,
                'memory_gb': 4,
                'disk_gb': 100,
            }

        # === 数据库配置 ===
        if 'database_heavy' in features or project_type in [ProjectType.DATABASE_APP, ProjectType.ECOMMERCE]:
            db_config = {
                'cpu_cores': 4,
                'memory_mb': 8000,
                'storage_gb': 200,
                'version': '8.0',
            }
        elif project_type in [ProjectType.WEB_BACKEND, ProjectType.WEB_FULLSTACK, ProjectType.MOBILE_BACKEND]:
            db_config = {
                'cpu_cores': 2,
                'memory_mb': 4000,
                'storage_gb': 100,
                'version': '8.0',
            }

        return cvm_config, db_config

    def _detect_primary_language(self) -> Optional[str]:
        """
        检测项目的主要编程语言

        Returns:
            主要编程语言字符串（如 'golang', 'python', 'nodejs'）
        """
        found_files = self.analysis_data.get('found_files', [])

        # 语言优先级映射（按特异性排序）
        language_priority = {
            'golang': 10,
            'rust': 9,
            'java_maven': 8,
            'java_gradle': 8,
            'nodejs': 7,
            'python_modern': 6,
            'python_setup': 5,
            'python_deps': 4,
            'php': 3,
            'ruby': 2,
        }

        # 找到优先级最高的语言
        best_language = None
        best_priority = -1

        for file_type in found_files:
            priority = language_priority.get(file_type, 0)
            if priority > best_priority:
                best_priority = priority
                best_language = file_type

        # 统一返回值
        if best_language:
            if best_language == 'golang':
                return 'golang'
            elif best_language in ['java_maven', 'java_gradle']:
                return 'java'
            elif best_language == 'nodejs':
                return 'nodejs'
            elif best_language in ['python_modern', 'python_setup', 'python_deps']:
                return 'python'
            elif best_language == 'rust':
                return 'rust'
            elif best_language == 'php':
                return 'php'
            elif best_language == 'ruby':
                return 'ruby'

        return None

    def _calculate_confidence(self, features: List[str]) -> float:
        """Calculate confidence based on detected features"""
        base_confidence = 0.5

        # More features = higher confidence
        if len(features) >= 5:
            base_confidence = 0.9
        elif len(features) >= 3:
            base_confidence = 0.8
        elif len(features) >= 2:
            base_confidence = 0.7
        elif len(features) >= 1:
            base_confidence = 0.6

        return base_confidence

    def _build_reasoning(self, project_type: ProjectType, features: List[str]) -> str:
        """Build human-readable reasoning"""
        lines = [
            f"检测到项目类型为 {project_type.value}",
            f"检测到的特征: {', '.join(features) if features else '无'}",
        ]
        return " | ".join(lines)

    def _create_default_requirement(self) -> CloudServiceRequirement:
        """Create default requirement when analysis fails"""
        return CloudServiceRequirement(
            project_type=ProjectType.GENERAL,
            required_services=[
                ServiceRequirement(
                    service_type=CloudServiceType.CVM,
                    required=True,
                    reason="默认配置"
                )
            ],
            cvm_config={'cpu_cores': 2, 'memory_gb': 4, 'disk_gb': 100},
            confidence=0.3,
            analysis_reasoning="无法分析仓库，使用默认配置"
        )


def analyze_cloud_services(repo_url: str, verbose: bool = False, model: str = 'deepseek', session_dir=None, use_api: bool = True) -> CloudServiceRequirement:
    """
    Convenience function to analyze repository and determine cloud service requirements

    Args:
        repo_url: GitHub repository URL
        verbose: Enable verbose logging
        model: AI model to use ('deepseek' or 'anthropic')
        session_dir: Optional session directory to store cloned repository
        use_api: Use GitHub API instead of cloning (default: True)

    Returns:
        CloudServiceRequirement object
    """
    analyzer = EnhancedResourceAnalyzer(repo_url, verbose=verbose, model=model, session_dir=session_dir, use_api=use_api)
    return analyzer.analyze()
