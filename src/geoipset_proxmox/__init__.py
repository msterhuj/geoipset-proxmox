"""
geoipset_proxmox - A script to manage GeoIP IP sets in Proxmox VE
"""
import click

from rich.table import Table
from rich.console import Console
from rich.traceback import install as install_traceback
install_traceback(show_locals=True)

from .static import PREFIX
from . import proxmox, dbip

console = Console()

@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to the configuration file.')
@click.pass_context
def cli(ctx: click.Context, config: str):
    """
    GeoIPSet Proxmox CLI for managing GeoIP IP sets in Proxmox VE.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = config if config else None

@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """
    Display the list of all countries IP sets in the Proxmox cluster.
    """
    config_path = ctx.obj.get('config')
    proxmox_client = proxmox.get_proxmox_client(config_path)
    ipsets = proxmox.get_proxmox_ipset(proxmox_client)
    table = Table(title="Proxmox GeoIP IP Sets")
    table.add_column("IP Set Name", justify="left", style="cyan")
    table.add_column("Number of cidr", justify="left", style="green")

    for name, cidrs in ipsets.items():
        table.add_row(name, str(len(cidrs)))

    console.print(table)

@cli.command()
@click.argument('country')
@click.pass_context
def sync(ctx: click.Context, country: str):
    """
    Add or update a new IP set for the specified country.
    :param country: The country code for the IP set.
    """
    config_path = ctx.obj.get('config')
    proxmox_client = proxmox.get_proxmox_client(config_path)

    # Split comma-separated country codes and strip whitespace
    country_codes = [PREFIX + cc.strip().lower() for cc in country.split(',')]
    dbip_dataset = dbip.get_latest_ip(
        [dbip.parse_mapping_key(country + "_v4")[0] for country in country_codes] + \
        [dbip.parse_mapping_key(country + "_v6")[0] for country in country_codes])


    for cc in country_codes:
        try:
            proxmox.sync_country_ipset(cc + "_v4", dbip_dataset, proxmox_client)
            proxmox.sync_country_ipset(cc + "_v6", dbip_dataset, proxmox_client)
        except Exception as e:
            console.print(f"Error syncing IP set for {cc}: {e}")

@cli.command()
@click.argument('country')
@click.pass_context
def remove(ctx: click.Context, country: str):
    """
    Remove IP sets for the specified country codes.
    :param country: Comma-separated country codes to remove IP sets for (e.g., 'US,DE' or 'fr,us').
    """
    config_path = ctx.obj.get('config')
    proxmox_client = proxmox.get_proxmox_client(config_path)

    # Split comma-separated country codes and strip whitespace
    country_codes = [PREFIX + cc.strip().lower() for cc in country.split(',')]

    for cc in country_codes:
        try:
            proxmox.delete_ipset(cc + "_v4", proxmox_client)
            proxmox.delete_ipset(cc + "_v6", proxmox_client)
        except ValueError as e:
            console.print(f"Error removing IP set {cc}: {e}")

def main():
    """
    Main entry point for the GeoIPSet Proxmox CLI.
    """
    cli(obj={})

if __name__ == "__main__":
    main()
