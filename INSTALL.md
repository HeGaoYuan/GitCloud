# GitCloud CLI Installation Guide

## Quick Installation

### Method 1: Install from pip (Recommended)

```bash
pip install gitcloud-cli
```

After installation, you can use the `gitcloud` command directly:

```bash
gitcloud --repo_url https://github.com/your/repo
```

### Method 2: Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/gitcloud-cli.git
cd gitcloud-cli

# Install in development mode
pip install -e .
```

### Method 3: Download pre-built executable

For users who don't want to install Python dependencies:

1. Download the executable for your platform:
   - **Linux**: `gitcloud-linux`
   - **Windows**: `gitcloud-windows.exe`
   - **macOS**: `gitcloud-macos`

2. Make it executable (Linux/macOS only):
   ```bash
   chmod +x gitcloud-linux
   ```

3. Run it:
   ```bash
   # Linux/macOS
   ./gitcloud-linux --repo_url https://github.com/your/repo

   # Windows
   gitcloud-windows.exe --repo_url https://github.com/your/repo
   ```

## Building Executables (For Developers)

If you want to build the executables yourself:

### Linux/macOS
```bash
./build_executable.sh
```

### Windows
```bash
build_executable.bat
```

The executables will be created in the `dist/` directory.

## Verification

After installation, verify that gitcloud is working:

```bash
# Check version and help
gitcloud --help

# Check clean command
gitcloud clean --help
```

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade gitcloud-cli
```

## Uninstalling

```bash
pip uninstall gitcloud-cli
```

## Troubleshooting

### Command not found

If you get "command not found" after installation:

1. Make sure pip's bin directory is in your PATH
2. Try running with python module syntax:
   ```bash
   python -m main --repo_url https://github.com/your/repo
   ```

### Module import errors

If you encounter module import errors, try reinstalling:

```bash
pip uninstall gitcloud-cli
pip install gitcloud-cli
```

Or install in development mode if you cloned the repository:

```bash
pip install -e .
```
