# GitCloud CLI

**GitCloud** is an intelligent cloud provisioning tool that analyzes GitHub projects and automatically provisions the required cloud resources to run them.

## Installation

```bash
git clone git@github.com:HeGaoYuan/GitCloud.git
pip install .
```

## Quick Start

### Basic Usage

```bash
# Provision a GitHub project to cloud
gitcloud --repo_url https://github.com/itzabhinavarya/ToDo-Application

# Another example
gitcloud --repo_url https://github.com/ichtrojan/go-todo
```

### Clean Up Resources

```bash
# List all sessions
gitcloud clean --list

# Clean up a specific session
gitcloud clean session_20250113_143022
```

## How It Works

1. **Analyze**: GitCloud analyzes your GitHub repository to determine required resources
2. **Configure**: On first run, you'll be prompted to enter:
   - AI model preference (DeepSeek or Anthropic)
   - API key
   - Cloud provider credentials (Tencent Cloud)
3. **Provision**: GitCloud provisions cloud resources (CVM, databases, etc.)
4. **Access**: Connect to your provisioned resources via SSH

All configuration is saved to `~/.gitcloud/config.json` for future use.

## Requirements

- Python 3.8+ (for pip installation)
- Tencent Cloud account with API access
- DeepSeek or Anthropic API key


## Current Limitations (Alpha Version)

⚠️ **GitCloud is in alpha stage** with the following limitations:

### Supported Languages
Currently, only the following languages are supported:
- **Node.js** (JavaScript/TypeScript)
- **Go** (Golang)

### Supported Cloud Services
Currently, only the following cloud services can be provisioned:
- **CVM** (Cloud Virtual Machine)
- **MySQL** Database

Projects requiring Redis, Object Storage, CDN, GPU, or other services are not yet supported.

### Repository Size Limit
- Maximum repository size: **200 MB**
- Repositories with 100+ branches will be rejected
- Larger repositories cannot be analyzed due to cloning overhead

### Recommended Test Repositories
Try these verified examples to get started:
```bash
# Node.js Todo Application
gitcloud --repo_url https://github.com/itzabhinavarya/ToDo-Application

# Go Todo API
gitcloud --repo_url https://github.com/ichtrojan/go-todo
```

## Important Notes

⚠️ **Cloud Charges**: Cloud resources may incur charges. Always monitor your cloud provider console and use the `gitcloud clean` command to remove resources.

🔒 **Privacy**: All credentials are stored locally in `~/.gitcloud/config.json` and never sent to external servers except official cloud provider APIs.