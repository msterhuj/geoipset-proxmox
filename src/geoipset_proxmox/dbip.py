"""
This module provides functionality to fetch the latest IP ranges
for specified country codes from DB-IP.
"""

from datetime import datetime
from ipaddress import ip_address, summarize_address_range
from csv import DictReader
from tempfile import NamedTemporaryFile
from io import TextIOWrapper
import gzip

from requests import get as requests_get

from geoipset_proxmox import PREFIX

def build_mapping_key(country_code: str, version: int) -> str:
    """
    Build a mapping key for the country code and IP version.
    :param country_code: The country code (e.g., 'us').
    :param version: The IP version (4 or 6).
    :return: A formatted string representing the mapping key.
    """
    return f"{PREFIX}{country_code.lower()}_v{version}"

def parse_mapping_key(mapping_key: str) -> tuple[str, int]:
    """
    Parse a mapping key to extract the country code and IP version.
    :param mapping_key: The mapping key (e.g., 'geoipset_proxmox_us_v4').
    :return: A tuple containing the country code and IP version.
    """
    parts = mapping_key.split('_')
    if len(parts) != 3 or not parts[2].startswith('v'):
        raise ValueError(f"Invalid mapping key format: {mapping_key}")
    country_code = parts[1]
    version = int(parts[2][1])
    return country_code, version

def get_latest_ip(country_code: list[str]) -> dict:
    """
    Fetch the latest IP ranges for the specified country codes from DB-IP.
    :param country_code: List of country codes to fetch IP ranges for (e.g., ['US', 'DE']).
    :return: A dictionary mapping country codes to their respective IP ranges.
    """
    file_suffix = '.csv.gz'
    url = 'https://download.db-ip.com/free/dbip-country-lite-' \
        + datetime.utcnow().strftime('%Y-%m') + file_suffix
    country_mapping = {}
    country_code = [cc.lower() for cc in country_code]
    http_response = requests_get(url)
    print(f"Fetching data from {url}... Status code: {http_response.status_code}")
    with NamedTemporaryFile(suffix=file_suffix, delete=False) as gzip_file:
        gzip_file.write(http_response.content)

    with gzip.GzipFile(gzip_file.name, 'rb') as csv_file_bytes:
        rows = DictReader(TextIOWrapper(csv_file_bytes),
                          fieldnames=("ip_start", "ip_end", "country"))
        for r in rows:
            cc = r['country'].lower()
            if cc not in country_code:
                continue
            ip_start = ip_address(r['ip_start'])
            ip_version = ip_start.version
            ip_end = ip_address(r['ip_end'])
            subnets = [nets.with_prefixlen for nets in summarize_address_range(ip_start, ip_end)]
            mapping_key = build_mapping_key(cc, ip_version)
            if mapping_key not in country_mapping:
                country_mapping[mapping_key] = []
            country_mapping[mapping_key].extend(subnets)
    return country_mapping
