# Helpers for Postgres Database and SqlAlchemy
import os
from functools import cached_property

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as _sessionmaker

from app import settings


class DBManager:
    _DB_CONN_FORMAT_HEAD = "postgresql+psycopg2://{user}:{password}@{host}:{port}/"
    _DB_CONN_ASYNC_FORMAT_HEAD = "postgresql+asyncpg://{user}:{password}@{host}:{port}/"

    DB_CONN_FORMAT = _DB_CONN_FORMAT_HEAD + '{name}'
    DB_CONN_ASYNC_FORMAT = _DB_CONN_ASYNC_FORMAT_HEAD + '{name}'
    DB_CONN_DEFAULT_FORMAT = _DB_CONN_FORMAT_HEAD + 'postgres'
    DB_CONN_DEFAULT_ASYNC_FORMAT = _DB_CONN_ASYNC_FORMAT_HEAD + 'postgres'

    @classmethod
    def create(cls, db_alias: str):
        """
        Gets a manager instance by DB alias, as defined as keys in
        `settings.DATABASES`

        Args:
            db_alias:

        Returns:

        """
        if db_alias not in settings.DATABASES:
            raise IndexError(f"DB Alias '{db_alias}' not found.")
        config = settings.DATABASES[db_alias]

        manager = cls(
            host=config.get('host', 'localhost'),
            port=config.get('port', 5432),
            user=config['user'],
            password=config['password'],
            name=config['name'],
            echo=config.get('echo', False),
            on_creation=config.get('on_creation')
        )
        if 'test' in config:
            test_config = config['test']
            test_manager = cls(
                host=test_config.get('host') or config.get('host', 'localhost'),
                port=test_config.get('host') or config.get('port', 5432),
                user=test_config.get('host') or config['user'],
                password=test_config.get('host') or config['password'],
                name=test_config.get('host') or config['name'],
                echo=test_config.get('host') or config.get('echo', False),
                on_creation=test_config.get('on_creation') or config.get('on_creation')
            )
            setattr(manager, '_test_manager', test_manager)
        return manager

    def __init__(self, host, port, user, password, name, echo, on_creation=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.name = name
        self.echo = echo
        self._conn_str = self.DB_CONN_FORMAT.format(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            name=self.name
        )
        self._async_conn_str = self.DB_CONN_ASYNC_FORMAT.format(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            name=self.name
        )
        self._test_manager = None
        self.on_creation = on_creation

    @property
    def test_manager(self) -> 'DBManager':
        return self._test_manager

    @property
    def conn_str(self):
        return self._conn_str

    @property
    def async_conn_str(self):
        return self._async_conn_str

    def create_db_if_not_exist(self):
        default_conn_str = self.DB_CONN_DEFAULT_FORMAT.format(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )
        engine_default = create_engine(
            default_conn_str,
            echo=self.echo
        )
        with engine_default.connect() as conn:
            conn.execute("COMMIT")
            try:
                stmt = text(f"CREATE DATABASE {self.name}")
                conn.execute(stmt)
                if self.on_creation:
                    for sql in self.on_creation:
                        conn.execute(sql)
            except:
                pass

    @cached_property
    def engine(self):
        return create_engine(self._conn_str, echo=self.echo)

    @cached_property
    def async_engine(self):
        return create_async_engine(
            self._async_conn_str, echo=self.echo
        )

    @property
    def sessionmaker(self):
        return _sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

    @property
    def async_sessionmaker(self):
        return _sessionmaker(
            self.async_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    def run_migrations(self) -> None:
        # config_file = os.path.join(
        #     settings.PROJECT_BASE_PATH,
        #     'app',
        #     'models',
        #     'alembic.ini'
        # )
        # alembicArgs = [
        #     '--raiseerr',
        #     '--config',
        #     config_file,
        #     'upgrade',
        #     'head',
        # ]
        # alembic.config.main(argv=alembicArgs)

        alembic_cfg = Config()
        alembic_cfg.set_main_option(
            'script_location',
            os.path.join(
                settings.PROJECT_BASE_PATH,
                'app',
                'models',
                'alembic',
            )
        )
        alembic_cfg.set_main_option('sqlalchemy.url', self._conn_str)
        command.upgrade(alembic_cfg, 'head')

    def create_all_tables_from_metadata(self, metadata):
        metadata.drop_all(bind=self.engine)
        metadata.create_all(bind=self.engine)

    def destroy_all_tables_from_metadata(self, metadata):
        metadata.drop_all(bind=self.engine)
