from sqlalchemy import Column, String, Text, Integer, SmallInteger, ForeignKey, Boolean, DateTime, func, text, \
    BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

from app.blockchains import BLOCKCHAIN_SOLANA

Base = declarative_base()


class NFTCollection(Base):
    __tablename__ = 'nft_collection'

    # Constants
    STATUS_INACTIVE = 0
    STATUS_ACTIVE = 1
    STATUS_DELETED = 2

    DATA_STATUS_UPDATING = 0  # Data related to this collection are being populated still
    DATA_STATUS_DONE = 1  # Data ready
    DATA_STATUS_FAILED = 2  # Something worth manually checking into.

    pk = Column("id", UUID(), primary_key=True, server_default=func.uuid_generate_v4())
    blockchain_id = Column(
        Integer(),
        index=True,
        nullable=False,
        default=BLOCKCHAIN_SOLANA
    )
    name = Column(String(length=100), index=True, nullable=True, default="")
    family = Column(String(length=100), index=True, default="")
    slug = Column(String(length=127), index=True, default="")
    description = Column(Text, default="")
    # For different chains, this will be the ID that can help uniquely identify
    # this collection. E.g., for Solana, this will be the `update_authority`.
    onchain_id = Column(String(length=127), index=True, default="")
    seller_fee_basis_points = Column(
        Integer(),
        default=0,
        comment="Unit in 1/10000th, can be overridden by individual NFT."
    )
    verified = Column(
        Boolean(),
        default=False,
    )
    data_status = Column(
        SmallInteger(),
        default=DATA_STATUS_UPDATING,
        comment="For storing the data update information for ingesting."
    )
    creators = Column(
        JSONB,
        nullable=True,
        comment="""In format: [{"creator": <>, "share": <>}, ...].
        Can be overridden by individual NFT.
        """
    )

    # TZ agnostic Timestamp
    created_at = Column(TIMESTAMP(), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(),
        server_default=func.now(),
        server_onupdate=func.now(),
        onupdate=func.now()
    )
    nsfw = Column(
        Boolean(),
        default=False,
        nullable=False,
        index=True
    )
    status = Column(
        SmallInteger(),
        index=True,
        default=STATUS_INACTIVE,
        nullable=False
    )
    # The date (roughly) that this collection is launched.
    # Inferred from the first NFT mint time stamp.
    launch_date = Column(
        DateTime(),
        nullable=True,
        default=None
    )

    nfts = relationship("NFT", backref="nft_collection")


class NFT(Base):
    __tablename__ = 'nft'

    pk = Column("id", UUID(), primary_key=True, server_default=func.uuid_generate_v4())
    nft_collection_id = Column(UUID(), ForeignKey("nft_collection.id"), index=True)
    token_address = Column(String(length=127), index=True, default="")
    name = Column(String(length=100), index=True, nullable=True, default="")
    slug = Column(String(length=127), index=True, default="")
    is_mutable = Column(Boolean(), default=True, nullable=False)
    description = Column(Text(), default="")
    metadata_uri = Column(Text(), default="")
    animation_url = Column(Text(), default="")
    external_url = Column(Text(), default="")
    seller_fee_basis_points = Column(
        Integer(),
        default=0,
        comment="Unit in 1/10000th, can be overridden by individual NFT."
    )
    creators = Column(
        JSONB(),
        nullable=True,
        comment="""In format: [{"creator": <>, "share": <>}, ...].
        Can be overridden by individual NFT.
        """
    )
    ext_data = Column(
        JSONB(),
        nullable=True,
        comment="""Extra data extracted from metadata content.
        """
    )
    rarity_score_1 = Column(
        String(length=16),
        nullable=True,
        default="",
        comment="A rarity score"
    )
    # TZ agnostic Timestamp
    created_at = Column(TIMESTAMP(), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(),
        server_default=func.now(),
        server_onupdate=func.now(),
        onupdate=func.now()
    )


class NFTAttributeDef(Base):
    __tablename__ = 'nft_attribute_def'

    pk = Column("id", Integer(), primary_key=True, autoincrement=True)
    # Which collection is this attribute definition for?
    nft_collection_id = Column(UUID(), ForeignKey("nft_collection.id"), index=True)
    name = Column(String(64), index=True, default='', nullable=False)
    value = Column(String(127), index=True, default='', nullable=False)
    # Some additional category data, e.g., Background, Facial Feature, etc
    # Just for better classification of things.
    cat1 = Column(String(64), default='', nullable=False)
    cat2 = Column(String(64), default='', nullable=False)
    # TZ agnostic Timestamp
    created_at = Column(TIMESTAMP(), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(),
        server_default=func.now(),
        server_onupdate=func.now(),
        onupdate=func.now()
    )


class NFTAttributes(Base):
    __tablename__ = 'nft_attributes'

    pk = Column(BigInteger(), autoincrement=True, primary_key=True)

    nft_id = Column(UUID(), ForeignKey("nft.id"), index=True)
    # nad = NFTAttributeDef
    nad_id = Column(Integer(), ForeignKey("nft_attribute_def.id"), index=True)


class NFTCollectionSubscriptions(Base):
    """
    Table for recording users' subcriptions to NFT collections.

    """
    __tablename__ = 'nft_collection_subscriptions'

    pk = Column(
        BigInteger(),
        primary_key=True,
        autoincrement=True
    )
    user_id = Column(
        UUID(),
        index=True,
        nullable=False,
        comment="Weak ref to User ID. This should be provided from external "
                "services such as User Service."
    )
    nft_collection_id = Column(
        UUID(),
        ForeignKey("nft_collection.id"),
        index=True
    )
    subscribed_at = Column(
        TIMESTAMP(),
        nullable=True,
        default=None
    )
    unsubscribed_at = Column(
        TIMESTAMP(),
        nullable=True,
        default=None
    )


class NFTUserPermissions(Base):
    """
    This is a subtable only locally scoped to NFT service. The entry creations
    in this table is triggered by User Service.

    Consider this table a subset of the main user table and only users present
    in this table has the access to NFT related services.

    What they are able to access is documented in this table.

    We have this subset of users in NFT database for fast lookup and it can
    help make NFT service more standalone.
    """
    __tablename__ = 'nft_user_permissions'
    __table_args__ = (
        UniqueConstraint('user_id', 'blockchain_id', name='user_blockchain_uniq'),
    )
    pk = Column(BigInteger(), autoincrement=True, primary_key=True)
    user_id = Column(
        UUID(),
        index=True,
        nullable=False,
        comment="Weak ref to User ID. This should be provided from external "
                "services such as User Service."
    )
    blockchain_id = Column(
        SmallInteger(),
        index=True,
        nullable=False,
        default=BLOCKCHAIN_SOLANA
    )
    # JSON data for the specific blockchain
    config = Column(
        JSONB(),
        nullable=True,
        default={}
    )


## TODO Use Postgres to store the Crawler info
#         * For transaction crawlers,
#
#         Data to store:
#             {
#             "h": "transaction_hash",
#             # composite data
#             "pk": S -> "m#<market_id>",
#             "sk": N -> "timestamp" (descending),
#             }