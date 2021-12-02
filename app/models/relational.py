from sqlalchemy import Column, String, Text, Integer, SmallInteger, ForeignKey, Boolean, DateTime, func, text, \
    BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

from app.blockchains import BLOCKCHAIN_SOLANA

Base = declarative_base()


class NFTCollection(Base):
    __tablename__ = 'nft_collection'

    pk = Column("id", UUID(), primary_key=True, server_default=func.uuid_generate_v4())
    blockchain = Column(
        SmallInteger(),
        index=True,
        nullable=False,
        default=BLOCKCHAIN_SOLANA
    )
    name = Column(String(length=100), index=True, nullable=True, default="")
    family = Column(String(length=100), index=True, default="")
    slug = Column(String(length=127), index=True, default="")
    description = Column(Text, default="")
    update_authority = Column(String(length=127), index=True, default="")
    seller_fee_basis_points = Column(
        Integer,
        default=0,
        comment="Unit in 1/10000th, can be overridden by individual NFT."
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
    nfts = relationship("NFT", backref="nft_collection")


class NFT(Base):
    __tablename__ = 'nft'

    pk = Column("id", UUID(), primary_key=True)
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
    name = Column(String(64), index=True, default='', nullable=False)
    value = Column(String(127), index=True, default='', nullable=False)
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

    pk = Column(BigInteger(), primary_key=True, autoincrement=True)
    nft_id = Column(UUID(), ForeignKey("nft.id"), index=True)
    # nad = NFTAttributeDef
    nad_id = Column(Integer(), ForeignKey("nft_attribute_def.id"), index=True)
