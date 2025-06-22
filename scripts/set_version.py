# Usage: python scripts/set_version.py 0.0.1
# This will update the version in pyproject.toml and labctl/__init__.py to argument passed to the script
# Default set to 0.0.0 if no argument is passed

from sys import argv
import re

def replace(file, pattern, replace):
    with open(file, "r") as f:
        content = f.read()
        content = re.sub(pattern, replace, content)
    with open(file, "w") as f:
        f.write(content)
    print(f"Updated {file} with new version {replace}")

version = "0.0.0"
if len(argv) > 1:
    version = argv[1]
    version = version.replace("v", "")

if not re.match(r"^\d+\.\d+\.\d+$", version):
    print("Invalid version format. Please use MAJOR.MINOR.PATCH format")
    exit(1)

print(f"Setting version to {version}")
replace("pyproject.toml", "version = \"[0-9.]+\"", f"version = \"{version}\"")
