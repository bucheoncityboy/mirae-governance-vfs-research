"""Interactive credential entry outside the repository, with terminal echo off."""
import argparse
import getpass
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--private-dir', required=True)
args = parser.parse_args()
directory = Path(args.private_dir).resolve()
repository = Path(__file__).resolve().parents[1]
if directory == repository or repository in directory.parents:
    raise SystemExit('Credential storage must be outside the repository')
directory.mkdir(parents=True, exist_ok=True, mode=0o700)
directory.chmod(0o700)
value = getpass.getpass('OpenDART API key (input hidden): ').strip()
if len(value) != 40 or not value.isalnum():
    raise SystemExit('Expected a 40-character API key; nothing saved')
file = directory / 'opendart-key'
flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
if hasattr(os, 'O_NOFOLLOW'):
    flags |= os.O_NOFOLLOW
fd = os.open(file, flags, 0o600)
try:
    os.fchmod(fd, 0o600)
    os.write(fd, value.encode())
finally:
    os.close(fd)
print('Credential configured outside Git; value is not displayed')
