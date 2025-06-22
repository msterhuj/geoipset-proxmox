"""
This module provides functionality to interact with Proxmox VE's firewall IP sets.
It includes functions to create, update, and delete IP sets based on GeoIP data.
"""
from datetime import datetime
from proxmoxer import ProxmoxAPI
from rich.progress import track
from . import config, PREFIX

def get_proxmox_client(config_path: str = None) -> ProxmoxAPI:
    """
    Create a ProxmoxAPI client using the configuration.
    :param config_path: Path to the configuration file. If None, it will use the environment
                        variable GEOIPSET_PROXMOX_CONFIG or default to './config.toml'.
    :return: An instance of ProxmoxAPI.
    """
    config_data = config.get_config(config_path).get('proxmox', {})
    return ProxmoxAPI(
        host=config_data.get("host", "localhost:8006"),
        user=config_data.get("user", "root@pam"),
        password=config_data.get("pass", ""),
        verify_ssl=config_data.get("verify_ssl", True)
    )

def get_proxmox_ipset(proxmox_client: ProxmoxAPI) -> dict:
    """
    Retrieve all existing IP sets from Proxmox starting with the PREFIX.
    :return: A dictionary where keys are IP set names and values are lists of CIDRs
    """
    ipsets: list = proxmox_client.cluster.firewall.ipset.get()
    dataset = {}
    for ipset in ipsets:
        ipset_name = ipset['name']
        if not ipset_name.startswith(PREFIX):
            continue
        dataset[ipset_name] = [
            item['cidr']
            for item in proxmox_client.cluster.firewall.ipset(ipset_name).get()
        ]
    return dataset

def sync_country_ipset(country_key: str, dbip_dataset: dict, proxmox_client: ProxmoxAPI) -> None:
    """
    Create / update and remove IP set for a specific country in accordance with the provided CIDRs and what is already in Proxmox.
    :param country: The country code for the IP set.
    :param cidrs: A list of CIDRs to be added to the IP set.
    :param proxmox_client: An instance of ProxmoxAPI.
    """
    proxmox_dataset = get_proxmox_ipset(proxmox_client)
    if country_key not in dbip_dataset:
        print(f"Country {country_key} not found in DB-IP dataset, skipping sync.")
        return

    # check if the ipset exists in Proxmox if not create it
    if country_key not in proxmox_dataset.keys():
        print(f"Creating new IP set for {country_key} in Proxmox")
        proxmox_client.cluster.firewall.ipset.create(
            name=country_key,
            comment="Created by geoip_proxmox",
        )
        proxmox_dataset[country_key] = []

    dbip_cidrs = [item.replace('/32', '') for item in dbip_dataset[country_key]]
    proxmox_cidrs = proxmox_dataset[country_key]

    deleted_ips = 0
    added_ips = 0

    # delete CIDRs that are in Proxmox but not in DB-IP
    for cidr in track(proxmox_cidrs, description=f"Clean Old IP set for: {country_key}"):
        if cidr not in dbip_cidrs:
            print(f"Removing CIDR {cidr}")
            proxmox_client.cluster.firewall.ipset(country_key).delete(cidr)
            proxmox_cidrs.remove(cidr)
            deleted_ips += 1

    # add CIDRs that are in DB-IP but not in Proxmox
    for cidr in track(dbip_cidrs, description=f"Adding New IP set for: {country_key}"):
        if cidr.endswith('/32'):
            cidr = cidr[:-3]
        if cidr not in proxmox_cidrs:
            print(f"Adding CIDR {cidr}")
            proxmox_client.cluster.firewall.ipset(country_key).create(
                cidr=cidr,
                comment="Added by geoip_proxmox at " + datetime.now().isoformat(),
            )
            proxmox_cidrs.append(cidr)
            added_ips += 1

    print(f"Sync complete for {country_key}.")
    print(f"Added {str(added_ips)}")
    print(f"Removed {str(deleted_ips)}")


def delete_ipset(ipset_name: str, proxmox_client: ProxmoxAPI) -> None:
    """
    Delete an IP set in Proxmox.
    :param ipset_name: The name of the IP set to delete.
    :param proxmox_client: An instance of ProxmoxAPI.
    """
    if not ipset_name.startswith(PREFIX):
        raise ValueError(f"IP set name must start with {PREFIX}")

    if ipset_name not in get_proxmox_ipset(proxmox_client):
        print(f"IP set {ipset_name} does not exist in Proxmox")
        return

    # proxmox api does not support deleting all CIDRs in one go, so we need to delete them one by one
    cidrs = proxmox_client.cluster.firewall.ipset(ipset_name).get()
    for cidr in track(cidrs, description=f"Deleting CIDRs from IP set: {ipset_name}"):
        proxmox_client.cluster.firewall.ipset(ipset_name).delete(cidr['cidr'])
        print(f"Deleted CIDR {cidr['cidr']}")

    proxmox_client.cluster.firewall.ipset(ipset_name).delete()
    print(f"Deleted IP set: {ipset_name}")
