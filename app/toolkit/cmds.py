import click

from .models import do_generate_meta
from .solana import (
    do_get_transaction as solana_do_get_transaction,
    do_get_transactions_for as solana_do_get_transactions_for,
)


@click.command(name="generate-meta")
@click.argument("schemas_file")
@click.argument("output_file")
def generate_meta(schemas_file, output_file):
    return do_generate_meta(schemas_file, output_file)


@click.command(name='get-txn')
@click.argument('signature')
@click.argument('filename')
def solana_get_transaction(signature, filename):
    """
    Get transaction data for the specified `signature`.
    """
    return solana_do_get_transaction(signature, filename)


@click.command(name='get-txn-for')
@click.argument('public_key')
@click.argument('filename')
@click.option('-l', '--limit', required=False, default=50, type=int)
@click.option('-b', '--before', required=False, default=None)
@click.option('-u', '--until', required=False, default=None)
def solana_get_transactions_for(public_key, filename, limit, before, until):
    """
    Get transactions for a public_key and stores them to `file_name`.
    """
    return solana_do_get_transactions_for(public_key, filename, limit, before, until)


@click.group()
def models():
    """
    Tools for helping with data models.
    """
    pass


@click.group()
def solana():
    """
    Tools for Solana blockchain.
    """
    pass


@click.group()
def toolkit():
    """
    Toolkit.
    """
    pass


models.add_command(generate_meta)

solana.add_command(solana_get_transaction)
solana.add_command(solana_get_transactions_for)

toolkit.add_command(solana)
toolkit.add_command(models)
