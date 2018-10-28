import os
import os.path
import functools
import logging
from typing import Union
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.query import Query
from sqlalchemy.ext.declarative import as_declarative


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class DBCore:
    def __init__(self, engine=None, declarative_base=None):
        # Setting up the declarative base
        self._session = None

        self.engine = engine
        self.ss = sessionmaker(engine)
        # If this errors:
        # self.ss = sessionmaker()

    # Setting up the environment.
    def bind(self, engine):
        self.engine = engine
        self.ss.bind(self.engine)

    @property
    def session(self):
        # REQUIRE ENGINE
        self.require_engine()
        if self._session is None:
            self._session = self.ss()
            # self._session.query = self.new_query
        return self._session

    """
    # Setting up our declarative base.
    # Tied into the Handler, so we can access session in our models.
    @property
    def Base(self):
        if self._Base is None:
            self._Base = self.create_base()
        return self._Base

    # Lets us use `db.File`, etc.
    def __getattr__(self, attr):
        for sc in self.Base.__subclasses__():
            if attr == sc.__name__:
                return sc
            if attr == sc.__name__.lower()+'s':
                return sc.query()
        else:
            raise AttributeError

    def create_base(self):
        @as_declarative()
        class Base:
            def __init__(subself, *args, **kwargs):
                super().__init__(*args, **kwargs)

            @property
            def session(subself):
                return self.session

            @classmethod
            def query(cls):
                return self.session.query(cls)

            @classmethod
            def get_or_create(cls, *args, **kwargs):
                cls_instance = self.session.query(cls).filter_by(**kwargs).one_or_none()
                if cls_instance is None:
                    cls_instance = cls(*args, **kwargs)
                # We need this or our changes aren't commited.
                # This is Real Annoying, though!
                return cls_instance

            def get(subself, id):
                inst = subself.query().filter_by(id=id).one()
                return inst

            def delete(subself):
                self.session.delete(subself)
                self.session.commit()
        return Base

    # Engine related things.
    def create_all(self):
        self.Base.metadata.create_all(self.engine)

    def require_engine(self):
        if self.engine is None:
            logging.critical("No database found. Bind an engine first.") 
            exit(1)
    """


db = DBCore(create_engine(DB_URI+find_database('.umptag.db')))


"""
def get_database_handle():
    db_uri = find_database()
    if db_uri is None:
        print("No database detected. Run `umptag init` first.")
        exit(1)
    return DBHandler(db_uri)
"""


def database_cognant(func, *args) -> functools.partial:
    # print("No database detected. Run `umptag init` first.")
    return functools.partial(func, db)
