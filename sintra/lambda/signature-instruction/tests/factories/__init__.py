import factory
from faker import Factory as FakerFactory
from src.model import Instruction, InnerInstructionsGroup, Transaction
import base58

faker = FakerFactory.create()


class InstructionFactory(factory.Factory):
    """Instruction factory."""

    class Meta:
        model = Instruction

    accounts = [
        "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
        "2frLu5jvCggutcriRPCwCosGov1RC7i1DVkJvnq492Hi",
        "FR6s8ix5g9PqRA6onriCAkjgx4NP5AtExBK5332SVN5R",
        "HzZviooFx7qre2suQUTRcFTSq1FjbAQz6GHgaaErupr8",
        "4GgEhWDzsY7cKSR1aLQnDUuCqaPFGucDAYVRVEtsqTvF",
        "D3wgcpWjAWR3GREbkyuGr3bNLHfdQsLr5hN2AvSP8pBi",
        "AwYaJ66cz7BgRK11NwNW8XzHYk5k5TCoNMvnMU6KZSTs",
        "8NwLAcyYikLG6jrQmrd3GJS2SDyMdmshGgAACCLDaxhe",
        "Fqc4ts9nN1Hp1mZR6CEx6yG7T4eZH8FN39ruAGc2fTuC",
        "11111111111111111111111111111111",
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "SysvarRent111111111111111111111111111111111",
        "nZpTd1f4EnLFxCG5d48TXx3foEh8J63GRKBMpKZKXbB",
        "JAn3D3yZ1Zb8hE4mzKM382psXfmaELsqWJYEBx1EYxcq",
        "4pUQS4Jo2dsfWzt3VgHXy3H6RYnEDd11oWPiaM2rdAPw",
        "SysvarC1ock11111111111111111111111111111111",
        "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
        "HZaWndaNWHFDd9Dhk5pqUUtsmoBCqzb1MLu3NAh1VX6B",
    ]
    data = base58.b58decode("2rC3pU6F2iSj")
    program = "HZaWndaNWHFDd9Dhk5pqUUtsmoBCqzb1MLu3NAh1VX6B"
    index = 0


class InnerInstructionFactory(factory.Factory):
    """InnerInstruction factory."""

    class Meta:
        model = Instruction

    accounts = [
        "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
        "D3wgcpWjAWR3GREbkyuGr3bNLHfdQsLr5hN2AvSP8pBi",
    ]
    data = base58.b58decode("3Bxs4eTRjETr5exf")
    program = "11111111111111111111111111111111"
    index = None


class InnerInstructionsGroupFactory(factory.Factory):
    """InnerInstructionsGroup factory."""

    class Meta:
        model = InnerInstructionsGroup

    index = 0
    instructions = factory.List(
        [factory.SubFactory(InnerInstructionFactory) for _ in range(2)]
    )


class TransactionFactory(factory.Factory):
    """Transaction factory."""

    class Meta:
        model = Transaction

    slot = 110382804
    meta = {}
    fee = 5000
    block_time = 1638838606
    instructions = factory.List(
        [factory.SubFactory(InstructionFactory) for _ in range(2)]
    )
    inner_instructions_groups = factory.List(
        [factory.SubFactory(InnerInstructionsGroupFactory) for _ in range(2)]
    )
    account_keys = []
    post_token_balances = [
        {
            "accountIndex": 1,
            "mint": "Fqc4ts9nN1Hp1mZR6CEx6yG7T4eZH8FN39ruAGc2fTuC",
            "owner": "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
            "uiTokenAmount": {
                "amount": "1",
                "decimals": 0,
                "uiAmount": 1.0,
                "uiAmountString": "1",
            },
        }
    ]
    signature = "vWJh84c573fzeYdb8xNVAXNu7uTCCNY6HjarN7i8eDHWBZJdvyS4hrH8sSd5GaGZzfUqSgKhhSCRMiFJmC863d3"
