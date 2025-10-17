# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitCloud is an intelligent cloud provisioning tool that analyzes GitHub projects and automatically provisions the required cloud resources to run them. It uses AI (DeepSeek or Anthropic) to analyze repository structure and content, then provisions appropriate cloud resources on Tencent Cloud.

**Current Status**: Alpha - supports Node.js and Go projects only, with CVM and MySQL as the only supported cloud services.

## Installation & Setup

```bash
# Install the package
pip install .

# Run GitCloud
gitcloud --repo_url https://github.com/owner/repo

# Clean up resources
gitcloud clean --list
gitcloud clean <session_id>
```

## Development Commands

### Testing
```bash
# Test Docker image recommendations
python test_docker_images.py

# Test Claude execution (requires provisioned resources)
python test_exec_claude.py
```

### Building & Distribution
```bash
# Build package
python -m build

# Install in development mode
pip install -e .
```

### Website Development
```bash
cd website
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Architecture

### Core Components

1. **Entry Points**
   - [main.py](main.py) - Main CLI entry point, handles user input, configuration, and orchestrates the full workflow
   - [cleanup.py](cleanup.py) - Session cleanup utility for removing cloud resources and local session data

2. **Analyzer Package** ([gitcloud/analyzer/](gitcloud/analyzer/))
   - [analyer.py](gitcloud/analyzer/analyer.py) - `EnhancedResourceAnalyzer` class that clones repos, analyzes project structure, and determines resource requirements using AI
   - [cloud_service_spec.py](gitcloud/analyzer/cloud_service_spec.py) - Defines `ProjectType` enum, `CloudServiceType` enum, and data classes for service requirements
   - [resource_spec.py](gitcloud/analyzer/resource_spec.py) - Defines `ResourceSpec` class for CPU/memory/storage specifications
   - [docker_images.py](gitcloud/analyzer/docker_images.py) - Maps project types to pre-built Docker images containing Claude Code CLI

3. **Provider Package** ([gitcloud/provider/](gitcloud/provider/))
   - [tencent/tencent.py](gitcloud/provider/tencent/tencent.py) - Main provisioning logic for Tencent Cloud (CVM + MySQL)
   - [tencent/network.py](gitcloud/provider/tencent/network.py) - VPC, subnet, and security group creation
   - [tencent/credentials.py](gitcloud/provider/tencent/credentials.py) - Credential management and SSH keypair generation

### Data Flow

1. **User Input** → `main.py` validates GitHub URL and loads/prompts for configuration
2. **Repository Analysis** → `EnhancedResourceAnalyzer` clones repo and sends files to AI for analysis
3. **AI Response** → Returns `CloudServiceRequirement` with project type and service specifications
4. **Resource Provisioning** → `tencent.py` creates VPC, CVM instance, MySQL database (if needed)
5. **Session Storage** → All resource IDs and credentials stored in `~/.gitcloud/sessions/<session_id>/`
6. **SSH Access** → User can connect to provisioned CVM with generated SSH key

### Session Management

Sessions are stored in `~/.gitcloud/sessions/session_<timestamp>/` with these files:
- `00_specification_info.txt` - Original AI analysis and resource specs
- `01_network_info.txt` - VPC, subnet, security group IDs
- `02_cvm_info.txt` - CVM instance details and connection info
- `03_mysql_info.txt` - MySQL connection details (if provisioned)
- `ssh_key` / `ssh_key.pub` - SSH keypair for CVM access

Configuration is stored in `~/.gitcloud/config.json` with API keys and cloud credentials.

### AI Integration

The analyzer uses two AI providers (configurable):
- **DeepSeek**: Default, more economical option
- **Anthropic**: Alternative Claude-based option

AI receives:
- Repository file tree
- Content of key files (README, package.json, go.mod, etc.)
- Dockerfile analysis

AI returns structured JSON with:
- Project type classification
- Required services (CVM, MySQL)
- CPU/memory/storage specifications
- Confidence scores and reasoning

### Cloud Resource Provisioning

The provisioning flow:
1. **Network Setup**: Create VPC with 2 subnets (for HA)
2. **Security Groups**: Create groups for CVM and MySQL with appropriate rules
3. **CVM Creation**: Launch instance with selected image, inject SSH key, install Docker
4. **MySQL Creation** (if needed): Launch MySQL instance in same VPC
5. **Wait for Ready**: Poll until instances are running and accessible

CVM instances are provisioned with Ubuntu + Docker, and the appropriate base image (Node.js or Go) is pulled automatically.

## Key Design Decisions

### Why Only Node.js and Go in Alpha?
The analyzer can detect many languages, but Docker images and provisioning scripts are only complete for Node.js and Go. To add a new language, you must:
1. Create base Docker image in [dockerfiles/](dockerfiles/) directory
2. Add image metadata to [docker_images.py](gitcloud/analyzer/docker_images.py)
3. Update `SUPPORTED_LANGUAGES` in [analyer.py](gitcloud/analyzer/analyer.py)

### Repository Size Limit
200MB limit enforced via git ls-remote branch counting. Larger repos would cause:
- Excessive AI analysis costs (sending too many files)
- Long cloning times
- Timeout issues

### Single Cloud Provider
Only Tencent Cloud is supported because:
- Initial development focused on Chinese market
- Tencent Cloud SDK well-documented for CVM + CDB (MySQL)
- Adding AWS/Azure/GCP requires implementing new provider modules in [gitcloud/provider/](gitcloud/provider/)

### Session-Based Resource Tracking
Each `gitcloud` run creates a new session directory rather than maintaining a database. This makes cleanup simple and portable, but means sessions are local to the machine that created them.

## Testing Approach

Tests are integration-focused:
- [test_docker_images.py](test_docker_images.py) - Validates image recommendations and Dockerfile generation
- [test_exec_claude.py](test_exec_claude.py) - Tests end-to-end SSH connection and command execution on provisioned CVM

To run the full integration test:
1. Provision a test repository with `gitcloud --repo_url <url>`
2. Extract the public IP and SSH key path from session files
3. Run `test_exec_claude.py` with those parameters

## Common Development Scenarios

### Adding a New Cloud Service Type
1. Add service enum to `CloudServiceType` in [cloud_service_spec.py](gitcloud/analyzer/cloud_service_spec.py)
2. Update `SUPPORTED_SERVICES` list in [analyer.py](gitcloud/analyzer/analyer.py)
3. Add provisioning logic to [tencent.py](gitcloud/provider/tencent/tencent.py)
4. Add cleanup logic to [cleanup.py](cleanup.py)

### Modifying AI Analysis Prompt
The main prompt is constructed in `EnhancedResourceAnalyzer._analyze_with_ai()` in [analyer.py](gitcloud/analyzer/analyer.py:300-500). The prompt includes:
- Project type taxonomy (from `ProjectType` enum)
- Available service types (from `CloudServiceType` enum)
- File tree and file contents
- Alpha version limitations

### Debugging Provisioning Issues
1. Check session directory: `~/.gitcloud/sessions/<session_id>/`
2. Review `00_specification_info.txt` for AI analysis
3. Check cloud provider console for resource status
4. Test SSH connection: `ssh -i ~/.gitcloud/sessions/<session_id>/ssh_key ubuntu@<ip>`
5. Review CVM logs via Tencent Cloud console

### Website Modifications
The [website/](website/) directory is a standalone static site:
- [index.html](website/index.html) - Main page with animated workflow
- [css/style.css](website/css/style.css) - Dark theme styling
- [js/main.js](website/js/main.js) - Animation logic

The website is purely informational and doesn't interact with the CLI tool.

## Important Constraints

### Alpha Version Limitations
- **Languages**: Only Node.js and Go
- **Services**: Only CVM and MySQL
- **Cloud**: Only Tencent Cloud
- **Repo Size**: Max 200MB
- **Branches**: Rejects repos with 100+ branches

These are enforced in [analyer.py](gitcloud/analyzer/analyer.py) validation methods.

### Credentials and Security
- All credentials stored in `~/.gitcloud/config.json` (local file)
- SSH private keys stored per-session in `~/.gitcloud/sessions/<session_id>/ssh_key`
- Private key permissions set to 0600 automatically
- No credentials are sent anywhere except official cloud provider APIs
- AI providers only receive repository content (no credentials)

### Resource Cleanup
Cloud resources incur charges. Always use `gitcloud clean` to remove resources when done. The cleanup script:
1. Reads resource IDs from session directory
2. Deletes instances (CVM, MySQL)
3. Deletes network resources (VPC, subnets, security groups)
4. Removes local session directory

Order matters: instances must be deleted before VPC/security groups.
