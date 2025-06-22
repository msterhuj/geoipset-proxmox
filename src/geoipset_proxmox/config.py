"""
Configuration reader for geoipset_proxmox
"""

import tomllib
import os

def get_config(config_path: str = None) -> dict:
    """
    Load configuration from a TOML file.
    :param config_path: Path to the configuration file. If None, it will use the environment
                        variable GEOIPSET_PROXMOX_CONFIG or default to './config.toml'.
    :return: Parsed configuration as a dictionary.
    :raises FileNotFoundError: If the configuration file does not exist.
    :raises tomllib.TOMLDecodeError: If the file is not a valid TOML file.
    """
    if config_path is None:
        # Use the environment variable if not provided
        config_path = os.getenv('GEOIPSET_PROXMOX_CONFIG', './config.toml')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'rb') as f:
        return tomllib.load(f)
