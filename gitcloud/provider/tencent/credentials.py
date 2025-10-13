import os
import json
import tempfile
import subprocess
from pathlib import Path

def get_tencent_credentials():
    """Get Tencent Cloud credentials from environment variables (set by main.py)"""
    # Environment variables should be set by main.py after prompting user
    secret_id = os.environ.get("TENCENT_SECRET_ID")
    secret_key = os.environ.get("TENCENT_SECRET_KEY")

    if secret_id and secret_key:
        return secret_id, secret_key

    # If not in environment, raise an error
    # (main.py should have prompted and set these)
    raise Exception("Tencent Cloud credentials not found in environment. Please run via main.py.")


def generate_ssh_keypair(session_dir=None):
    """
    Generate SSH key pair for passwordless authentication

    Args:
        session_dir: Optional Path object for session directory. If provided, keys will be stored there.
                    Otherwise, uses temporary directory.

    Returns:
        Tuple of (private_key_path, public_key_content)
    """
    # Use session directory if provided, otherwise use temp directory
    if session_dir:
        key_dir = Path(session_dir)
        key_dir.mkdir(parents=True, exist_ok=True)
    else:
        key_dir = Path(tempfile.mkdtemp())

    private_key_path = key_dir / "ssh_key"
    public_key_path = key_dir / "ssh_key.pub"

    # Generate SSH key pair (Ed25519 for better security)
    subprocess.run([
        "ssh-keygen", "-t", "ed25519", "-f", str(private_key_path),
        "-N", "",  # No passphrase
        "-C", "gitcloud@tencent"
    ], check=True, capture_output=True)

    # Read public key
    with open(public_key_path, 'r') as f:
        public_key = f.read().strip()

    # Set proper permissions on private key
    os.chmod(private_key_path, 0o600)

    return str(private_key_path), public_key