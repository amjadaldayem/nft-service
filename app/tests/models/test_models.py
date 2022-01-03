import asyncio
import unittest

from sqlalchemy import text

from app.models.manager import DBManager
from app.models.models import NFTCollection, Base


class NftModelsTestCase(unittest.IsolatedAsyncioTestCase):
    use_default_loop = True
    TEST_DB_NAME = 'nft_test'

    test_db_manager = None  # type: DBManager

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_db_manager = DBManager.create('nft').test_manager
        cls.test_db_manager.create_db_if_not_exist()
        cls.test_db_manager.create_all_tables_from_metadata(Base.metadata)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test_db_manager.destroy_all_tables_from_metadata(Base.metadata)

    @classmethod
    def sessionmaker(cls):
        return cls.test_db_manager.async_sessionmaker()

    async def test_create(self):
        async with self.sessionmaker() as session:
            async with session.begin():
                session.add(
                    NFTCollection(name="c1")
                )
                session.add_all(
                    [
                        NFTCollection(name="c2"),
                        NFTCollection(name="c3"),
                    ]
                )
            await session.commit()
            session.query()
            result = await session.execute(text("SELECT COUNT(1) FROM nft_collection;"))
            c = result.scalars().first()
            print(c)
