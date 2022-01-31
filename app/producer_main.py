# Entry point for Kinesis producers for event captures

import click

from app.indexers.solana import solana_sme


@click.group()
def main():
    pass


main.add_command(solana_sme)

if __name__ == '__main__':
    main()
