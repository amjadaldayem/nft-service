import unittest

from sqlalchemy import text
from sqlalchemy.future import select

from app.models.manager import SQLDBManager
from app.models.models import NFTCollection, Base, NFT


class NftModelsTestCase(unittest.TestCase):
    use_default_loop = True
    TEST_DB_NAME = 'nft_test'

    test_db_manager = None  # type: SQLDBManager

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_db_manager = SQLDBManager.create('nft').test_manager
        cls.test_db_manager.create_db_if_not_exist()
        cls.test_db_manager.create_all_tables_from_metadata(Base.metadata)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test_db_manager.destroy_all_tables_from_metadata(Base.metadata)
        cls.test_db_manager.drop_db_if_exists()

    @classmethod
    def sessionmaker(cls):
        return cls.test_db_manager.sessionmaker()

    def test_sql_alchemy_basic_code(self):
        nfts = [
            NFT(name="c1-a"),
            NFT(name="c1-b")
        ]
        nft_collection_1 = NFTCollection(name="c1")
        nft_collection_1.nfts.extend(nfts)

        all_collections = [
            nft_collection_1,
            NFTCollection(name="c2"),
            NFTCollection(name="c3"),
        ]

        with self.sessionmaker() as session:
            session.add(all_collections[0])
            session.add_all(all_collections[1:])

            session.commit()
            c = session.execute(select(NFTCollection).where(
                NFTCollection.name == 'c1'
            ))
            actual = c.scalar()
            self.assertEqual(actual.name, 'c1')
            self.assertIsInstance(actual, NFTCollection)
            self.assertEqual(len(actual.nfts), 2)
            self.assertIsNotNone(actual.nfts[0].pk)
            self.assertIsNotNone(actual.nfts[1].pk)

            d = session.execute(select(NFTCollection).where(
                NFTCollection.name == 'none-existent'
            ))
            actual = d.scalar()
            self.assertFalse(actual)

            es = session.execute(select(NFTCollection).where(
                NFTCollection.name.like('c%')
            ))
            actual = [c.name for c in es.unique().scalars().all()]
            self.assertCountEqual(
                actual,
                [c.name for c in all_collections]
            )

    def test_sql_alchemy_exception_handling(self):
        class TestException(Exception):
            pass

        nft_collection = NFTCollection(name="shoud-not-persist")

        with self.assertRaises(TestException):
            with self.sessionmaker() as session:
                with session.begin():
                    session.add(nft_collection)
                    raise TestException("Something wrong")
                d = session.execute(
                    select(NFTCollection).where(
                        NFTCollection.name == nft_collection.name
                    )
                )
                self.assertIsNone(d.scalar())

        r = self.test_db_manager.engine.execute(
            text("SELECT * FROM nft_collection WHERE name = :name"),
            {'name': nft_collection.name}
        ).scalar()
        self.assertIsNone(r)
