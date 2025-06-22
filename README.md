# GeoIPSet for Proxmox

This permits you to create ipset on proxmox cluster to block or allow traffic from specific countries.

## Usage

```shell
geoipset-proxmox
```

```shell
Usage: geoipset-proxmox [OPTIONS] COMMAND [ARGS]...

  GeoIPSet Proxmox CLI for managing GeoIP ipsets in Proxmox VE.

Options:
  -c, --config PATH  Path to the configuration file.
  --help             Show this message and exit.

Commands:
  remove  Remove IP sets for the specified country codes.
  status  Display the list of all countries' IP sets in the Proxmox cluster.
  sync    Add or update a new IP set for the specified country.
```

## Configuration

Create a `config.toml` file in the root directory of the project with the following structure (example available in `config.example.toml`):

```toml
[proxmox]
host = "127.0.0.1:8006"
user = "root@pam"
pass = ""
verify_ssl = true
````

## Installation

You can install the package using pip:

```shell
pip install geoipset-proxmox
```
