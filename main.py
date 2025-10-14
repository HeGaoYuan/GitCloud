#!/usr/bin/env python3
"""
GitCloud CLI - Analyze GitHub projects and provision cloud resources
---------------------------------------------------------------------
Main entry point that integrates analyzer and cloud provider.

Usage:
    python main.py https://github.com/owner/repo
    python main.py https://github.com/owner/repo --provider tencent --region ap-guangzhou
    python main.py https://github.com/owner/repo --model deepseek --api-key YOUR_KEY
"""

import argparse
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Add gitcloud to path
sys.path.insert(0, str(Path(__file__).parent))

from gitcloud.analyzer.analyer import analyze_cloud_services

class Colors:
    """ANSI color codes for terminal output"""
    # Main colors
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'

    # Styles
    DIM = '\033[2m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    # Log level colors (inspired by npm)
    STEP = '\033[1;36m'      # Bold Cyan for STEP headers
    SUCCESS = '\033[1;32m'   # Bold Green for success
    ERROR = '\033[1;31m'     # Bold Red for errors
    WARNING = '\033[1;33m'   # Bold Yellow for warnings
    INFO = '\033[96m'        # Cyan for informational
    DEBUG = '\033[2;37m'     # Dim White for debug/verbose
    CONFIG = '\033[95m'      # Magenta for configuration


def print_colored(text, color=''):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.RESET}")


def print_step(text):
    """Print a STEP header"""
    print(f"\n{Colors.STEP}{'='*70}{Colors.RESET}")
    print(f"{Colors.STEP}{text}{Colors.RESET}")
    print(f"{Colors.STEP}{'='*70}{Colors.RESET}")


def print_config(label, value):
    """Print configuration item"""
    print(f"{Colors.CONFIG}  {label}: {Colors.RESET}{value}")


def print_substep(text):
    """Print a sub-step (indented)"""
    print(f"{Colors.INFO}  {text}{Colors.RESET}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.SUCCESS}{text}{Colors.RESET}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.ERROR}{text}{Colors.RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}{text}{Colors.RESET}")


def print_debug(text):
    """Print debug/verbose message"""
    print(f"{Colors.DEBUG}{text}{Colors.RESET}")


def clean_input(prompt=''):
    """
    Get input from user with cleaned stdin buffer to prevent using previous inputs
    """
    import sys
    import termios

    # Flush stdin buffer
    try:
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except:
        pass

    return input(prompt)


def show_banner():
    """Display GitCloud banner"""
    # Embedded banner as fallback
    BANNER = """
  ██████╗ ██╗████████╗ ██████╗██╗      ██████╗ ██╗   ██╗██████╗
 ██╔════╝ ██║╚══██╔══╝██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗
 ██║  ███╗██║   ██║   ██║     ██║     ██║   ██║██║   ██║██║  ██║
 ██║   ██║██║   ██║   ██║     ██║     ██║   ██║██║   ██║██║  ██║
 ╚██████╔╝██║   ██║   ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝
  ╚═════╝ ╚═╝   ╚═╝    ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝


  Run GitHub in Cloud Intelligently
"""

    # Try multiple locations for banner.txt
    possible_paths = [
        Path(__file__).parent / 'banner.txt',  # Development mode
        Path(__file__).parent.parent / 'banner.txt',  # Installed mode (one level up)
    ]

    # Try file paths first
    for banner_path in possible_paths:
        if banner_path.exists():
            try:
                with open(banner_path, 'r', encoding='utf-8') as f:
                    print(f.read())
                return
            except:
                pass

    # Fallback to embedded banner
    print(BANNER)


def show_disclaimer():
    """Show important disclaimers and warnings"""
    print("\n" + "="*70)
    print("⚠️  IMPORTANT DISCLAIMERS")
    print("="*70)
    print()
    print("⚠️  ALPHA SOFTWARE WARNING:")
    print("   GitCloud is currently in ALPHA stage. There may be bugs including:")
    print("   - Cloud resources being provisioned but not properly released")
    print("   - Unexpected charges from cloud providers")
    print("   - Incomplete cleanup of resources")
    print()
    print("   YOU ASSUME ALL RISKS AND CONSEQUENCES of using this software.")
    print("   Please monitor your cloud provider console for active resources.")
    print()
    print("🔒 PRIVACY & SECURITY:")
    print("   This software requires API keys and cloud credentials.")
    print("   ✓ Your keys and credentials are NEVER sent to any backend server")
    print("   ✓ All operations run locally on your machine")
    print("   ✓ Keys are only used to communicate directly with cloud providers")
    print()
    print("="*70)
    print()


def load_config():
    """Load configuration from ~/.gitcloud/config.json"""
    config_file = Path.home() / ".gitcloud" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Failed to read config file: {e}")
    return {}


def save_config(config):
    """Save configuration to ~/.gitcloud/config.json"""
    config_dir = Path.home() / ".gitcloud"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"⚠️  Failed to save config file: {e}")


def select_option(prompt, options):
    """
    Interactive option selector using arrow keys

    Args:
        prompt: The prompt to display
        options: List of (display_text, value) tuples

    Returns:
        The selected value
    """
    import sys
    import tty
    import termios

    selected = 0
    first_draw = True

    def display_menu():
        nonlocal first_draw

        if not first_draw:
            # Move cursor up to start of menu (including prompt line)
            sys.stdout.write(f"\033[{len(options) + 1}A")

        # Clear and draw prompt
        sys.stdout.write('\r\033[K')
        sys.stdout.write(f"{prompt}\n")

        # Draw options
        for i, (display_text, _) in enumerate(options):
            sys.stdout.write('\r\033[K')  # Clear line
            if i == selected:
                sys.stdout.write(f"  → {display_text}\n")
            else:
                sys.stdout.write(f"    {display_text}\n")

        sys.stdout.flush()
        first_draw = False

    # Display initial menu
    print()  # Add blank line before menu
    display_menu()

    # Get terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        while True:
            ch = sys.stdin.read(1)

            # Arrow keys send escape sequences: \x1b[A (up), \x1b[B (down)
            if ch == '\x1b':
                next1 = sys.stdin.read(1)
                next2 = sys.stdin.read(1)
                if next1 == '[':
                    if next2 == 'A':  # Up arrow
                        selected = (selected - 1) % len(options)
                        display_menu()
                    elif next2 == 'B':  # Down arrow
                        selected = (selected + 1) % len(options)
                        display_menu()

            # Enter key (both \r and \n)
            elif ch in ('\r', '\n'):
                break

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    print()  # New line after selection
    return options[selected][1]


def get_model_and_api_key(args):
    """Get model and api_key from args or config, prompt if not available"""
    config = load_config()
    config_file = Path.home() / ".gitcloud" / "config.json"

    # Get model
    model = args.model
    if not model:
        model = config.get('model')

    if not model:
        print("\n" + "="*70)
        print("🤖 Model Selection")
        print("="*70)
        print("Use ↑/↓ arrow keys to select, press ENTER to confirm:\n")

        options = [
            ("deepseek (DeepSeek API)", "deepseek"),
            ("anthropic (Anthropic Claude)", "anthropic")
        ]

        model = select_option("Select AI Model:", options)

        # Save to config
        config['model'] = model
        save_config(config)
        print(f"✅ Model '{model}' saved to {config_file}\n")

    # Get API key
    api_key = args.api_key
    if not api_key:
        api_key = config.get('api_key')

    if not api_key:
        print("🔑 API Key Required")
        print(f"Please enter your API key for {model}:")
        api_key = clean_input("> ").strip()

        if not api_key:
            print("❌ API key is required")
            sys.exit(1)

        # Ask if user wants to save the key
        print(f"\nSave API key to {config_file}?")
        save_key = clean_input("Press ENTER to save, or type 'n' to skip: ").strip().lower()
        if save_key != 'n':
            config['api_key'] = api_key
            save_config(config)
            print(f"✅ API key saved to {config_file}\n")
        else:
            print("⚠️  API key not saved (you'll need to enter it next time)\n")

    return model, api_key


def get_provider(args):
    """Get cloud provider from args or config, prompt if not available"""
    config = load_config()
    config_file = Path.home() / ".gitcloud" / "config.json"

    # Get provider
    provider = args.provider
    if not provider:
        provider = config.get('provider')

    if not provider:
        print("\n" + "="*70)
        print("☁️  Cloud Provider Selection")
        print("="*70)
        print("Use ↑/↓ arrow keys to select, press ENTER to confirm:\n")

        options = [
            ("Tencent Cloud", "tencent")
        ]

        provider = select_option("Select Cloud Provider:", options)

        # Save to config automatically
        config['provider'] = provider
        save_config(config)
        print(f"✅ Provider '{provider}' saved to {config_file}\n")

    return provider


def get_cloud_credentials(provider):
    """Get cloud provider credentials from config or prompt user"""
    config = load_config()
    config_file = Path.home() / ".gitcloud" / "config.json"
    credentials_key = f'{provider}_credentials'
    credentials = config.get(credentials_key, {})

    if provider == 'tencent':
        secret_id = credentials.get('secret_id')
        secret_key = credentials.get('secret_key')

        if not secret_id or not secret_key:
            print("\n" + "="*70)
            print("🔑 Tencent Cloud Credentials Required")
            print("="*70)
            print("Please enter your Tencent Cloud credentials:")
            secret_id = clean_input("Secret ID: ").strip()
            secret_key = clean_input("Secret Key: ").strip()

            if not secret_id or not secret_key:
                print("❌ Cloud credentials are required")
                sys.exit(1)

            # Ask if user wants to save
            print(f"\nSave credentials to {config_file}?")
            save_creds = clean_input("Press ENTER to save, or type 'n' to skip: ").strip().lower()
            if save_creds != 'n':
                config[credentials_key] = {
                    'secret_id': secret_id,
                    'secret_key': secret_key
                }
                save_config(config)
                print(f"✅ Credentials saved to {config_file}\n")
            else:
                print("⚠️  Credentials not saved (you'll need to enter them next time)\n")

        return secret_id, secret_key

    return None


def main():
    parser = argparse.ArgumentParser(
        description='GitCloud - Run GitHub projects in cloud intelligently',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze and provision with defaults
  gitcloud --repo_url https://github.com/ichtrojan/go-todo

  # Specify provider and region
  gitcloud --repo_url https://github.com/ichtrojan/go-todo --provider tencent --region ap-guangzhou

  # Specify model and API key
  gitcloud --repo_url https://github.com/ichtrojan/go-todo --model deepseek --api-key YOUR_KEY

  # Clean up a session
  gitcloud clean session_20250113_143022
        """
    )

    # Add subparsers for clean command
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Clean subcommand
    clean_parser = subparsers.add_parser('clean', help='Clean up a session')
    clean_parser.add_argument('session_id', type=str, nargs='?', help='Session ID to clean up')
    clean_parser.add_argument('--keep-logs', action='store_true',
                             help='Keep session log files, only delete SSH keys and cloud resources')
    clean_parser.add_argument('--local-only', action='store_true',
                             help='Only clean up local files, do not touch cloud resources')
    clean_parser.add_argument('--list', action='store_true',
                             help='List all available sessions')

    # Main command arguments
    parser.add_argument('--repo_url', '--repo-url', type=str, dest='repo_url',
                       help='GitHub repository URL')
    parser.add_argument('--provider', type=str,
                       choices=['tencent'],
                       help='Cloud provider (will prompt if not specified)')
    parser.add_argument('--region', type=str, default='na-siliconvalley',
                       help='Cloud region (default: na-siliconvalley)')
    parser.add_argument('--model', type=str, choices=['deepseek', 'anthropic'],
                       help='AI model provider (deepseek or anthropic)')
    parser.add_argument('--api-key', type=str,
                       help='API key for the AI model')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze project, do not provision resources')

    args = parser.parse_args()

    # Handle clean command
    if args.command == 'clean':
        # Import and run cleanup
        import cleanup
        return cleanup.main_with_args(args)

    # Show banner at the beginning (before any user interaction)
    show_banner()
    print()

    # Validate repo_url for main command - prompt if not provided
    if not args.repo_url:
        print("\n" + "="*70)
        print("📦 GitHub Repository URL")
        print("="*70)
        print("Please enter the GitHub repository URL:")
        print("Example: https://github.com/ichtrojan/go-todo")
        print()
        repo_url = clean_input(f"{Colors.CYAN}GitHub URL> {Colors.RESET}").strip()

        if not repo_url:
            print_error("\n❌ GitHub repository URL is required")
            sys.exit(1)

        args.repo_url = repo_url
        print()

    # Set github_url for backward compatibility
    args.github_url = args.repo_url

    try:
        # Confirmation prompt
        print("="*70)
        print("Press ENTER to continue...")
        print("="*70)
        input()

        # Show disclaimers
        show_disclaimer()
        print_colored("To proceed, please type: Yes, I understand", Colors.CYAN)
        user_input = clean_input(f"{Colors.CYAN}> {Colors.RESET}").strip()

        if user_input != "Yes, I understand":
            print_colored("\n❌ Risk acknowledgment required. Operation cancelled.", Colors.RED)
            print_colored("You must type exactly: Yes, I understand", Colors.YELLOW)
            return 0
        print()

        # Get model and API key
        model, api_key = get_model_and_api_key(args)

        # Get cloud provider
        provider = get_provider(args)

        # Get cloud provider credentials
        cloud_secret_id, cloud_secret_key = get_cloud_credentials(provider)

        # Configuration Summary
        print(f"\n{Colors.CONFIG}{'='*70}{Colors.RESET}")
        print(f"{Colors.CONFIG}📋 Configuration Summary{Colors.RESET}")
        print(f"{Colors.CONFIG}{'='*70}{Colors.RESET}")
        print_config("GitHub URL", args.github_url)
        print_config("Provider", provider)
        print_config("Region", args.region)
        print_config("Model", model)
        print(f"{Colors.CONFIG}{'='*70}{Colors.RESET}")

        # Create session directory for this run
        import time
        session_base = Path.home() / ".gitcloud" / "session"
        session_base.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        session_dir = session_base / f"session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        session_name = f"session_{timestamp}"

        # Print session info immediately
        print("\n" + "="*70)
        print(f"📁 Session Directory Created: {session_dir}")
        print(f"   Session ID: {session_name}")
        print("   All files for this session will be stored here.")
        print("="*70 + "\n")

        # Step 1: Analyze GitHub project
        print_step("STEP 1: Analyzing GitHub Project")

        # Set API key in environment for analyzer to use
        import os
        os.environ['ANTHROPIC_API_KEY'] = api_key

        result = analyze_cloud_services(args.github_url, verbose=True, model=model, session_dir=session_dir)
        docker_image = ""

        print_step("STEP 2: Analysis Results")
        print_config("Project Type", result.project_type.value)
        print_config("Project Subtype", result.project_subtype or 'N/A')
        if result.primary_language:
            print_config("Primary Language", result.primary_language)
        print_config("Required Services", f"{len(result.required_services)} services")
        for svc in result.required_services:
            specs = []
            if svc.cpu_cores:
                specs.append(f"{svc.cpu_cores} CPU")
            if svc.memory_gb:
                specs.append(f"{svc.memory_gb}GB RAM")
            if svc.disk_gb:
                specs.append(f"{svc.disk_gb}GB Disk")
            if svc.gpu_required:
                specs.append(f"GPU: {svc.gpu_type}")
            spec_str = ", ".join(specs) if specs else "default"
            print(f"  {Colors.INFO}- {svc.service_type.value}: {Colors.RESET}{spec_str}")
        print_config("Confidence", f"{result.confidence:.2f}")
        print_config("Reasoning", result.analysis_reasoning)

        # 显示推荐的 Docker 镜像
        docker_image = result.get_recommended_docker_image()
        print(f"\n{Colors.INFO}🐳 Recommended Docker Image:{Colors.RESET}")
        print(f"  {Colors.CONFIG}Base: {Colors.RESET}{docker_image['image']}")
        print(f"  {Colors.CONFIG}Description: {Colors.RESET}{docker_image['description']}")
        print(f"  {Colors.CONFIG}Includes:{Colors.RESET}")
        for item in docker_image['includes']:
            print(f"    {Colors.DIM}- {item}{Colors.RESET}")

        # Convert to provider spec (tencent format)
        provider_spec = result.to_tencent_spec(region=args.region)

        print_step("STEP 3: Provider Specification")
        print_debug(json.dumps(provider_spec, indent=2))

        # Stop here if analyze-only
        if args.analyze_only:
            print_success("\n✅ Analysis completed (--analyze-only mode)")
            return 0

        # Step 4: Confirm provisioning
        print_step("STEP 4: Resource Provisioning Confirmation")
        print_warning("\n⚠️  CLOUD RESOURCE PROVISIONING WARNING")
        print("This will create real cloud resources that may incur charges.")
        print("\nResources to be created:")
        if provider_spec.get('cvm'):
            cvm = provider_spec['cvm']
            print(f"  {Colors.INFO}• CVM: {Colors.RESET}{cvm.get('cpu_cores')} CPU, {cvm.get('memory_gb')} GB RAM, {cvm.get('disk_gb')} GB Disk")
            if cvm.get('gpu_type'):
                print(f"    {Colors.INFO}GPU: {Colors.RESET}{cvm.get('gpu_type')}")
        if provider_spec.get('mysql'):
            mysql = provider_spec['mysql']
            print(f"  {Colors.INFO}• MySQL: {Colors.RESET}{mysql.get('cpu_cores')} CPU, {mysql.get('memory_mb')} MB RAM, {mysql.get('storage_gb')} GB Storage")
        print(f"{Colors.STEP}{'='*70}{Colors.RESET}")

        confirm = clean_input("\nProceed with provisioning? Press ENTER to confirm, or type 'n' to cancel: ").strip().lower()
        if confirm == 'n' or confirm == 'no':
            print_error("❌ Provisioning cancelled by user")
            return 0

        # Step 5: Provision cloud resources
        print_step("STEP 5: Provisioning Cloud Resources")

        # Save spec to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(provider_spec, f, indent=2)
            spec_file = f.name

        try:
            # Build command based on provider
            if provider == 'tencent':
                provider_script = Path(__file__).parent / 'gitcloud' / 'provider' / 'tencent' / 'tencent.py'
                cmd = [
                    sys.executable,
                    str(provider_script),
                    '--analyzer-spec', spec_file,
                    '--base_image', docker_image['image'],
                    '--repo', args.github_url,
                    '--model', model,
                    '--api-key', api_key,
                    '--session-dir', str(session_dir)
                ]

            # Hide API key in command display
            cmd_display = cmd.copy()
            for i, arg in enumerate(cmd_display):
                if i > 0 and cmd_display[i-1] == '--api-key':
                    cmd_display[i] = '***'

            print_substep("🔧 Running provisioning command...")
            print_debug(f"Provider: {provider}, Region: {args.region}\n")

            # Set environment variables for cloud credentials
            env = subprocess.os.environ.copy()
            if provider == 'tencent':
                env['TENCENT_SECRET_ID'] = cloud_secret_id
                env['TENCENT_SECRET_KEY'] = cloud_secret_key

            # Run provisioning
            result = subprocess.run(cmd, check=False, env=env)

            if result.returncode == 0:
                print_success("\n" + "="*70)
                print_success("✅ GitCloud provisioning completed successfully!")
                print_success("="*70)
            else:
                print_error("\n" + "="*70)
                print_error(f"❌ Provisioning failed with exit code {result.returncode}")
                print_error("="*70)
                return result.returncode

        finally:
            # Clean up temp file
            Path(spec_file).unlink(missing_ok=True)

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
