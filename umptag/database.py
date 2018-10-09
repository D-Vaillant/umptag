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

def find_database():
    cur = os.path.abspath(os.path.curdir)
    db = os.path.join(cur, '.umptag.db')
    if os.path.exists(db):
        return db
    cur, child = os.path.dirname(cur), cur  # go up the hierarchy
    while cur != child:  # because the parent dir of '/' is '/'
        db = os.path.join(cur, '.umptag.db')
        if os.path.exists(db):
            return db
        cur, child = os.path.dirname(cur), cur  # go up the hierarchy
    return None


class DBHandler:
    DB_URI = "sqlite:///"

    def __init__(self, db_loc=None):
        # Setting up the declarative base
        self._Base = None
        self._session = None
        self.db_loc = db_loc

        # Allows us to define the engine later.
        if self.db_loc is not None:
            self.bind(self.db_loc)
        else:
            self.engine = None
            self.ss = sessionmaker()

    # Setting up the environment.
    def bind(self, db_uri):
        self.db_loc = db_uri
        self.engine = create_engine(self.DB_URI+db_uri)
        self.ss = sessionmaker(bind=self.engine)

    @property
    def session(self):
        # REQUIRE ENGINE
        self.require_engine()
        if self._session is None:
            self._session = self.ss()
            # self._session.query = self.new_query
        return self._session

    def new_query(self, *args):
        q = Query(*args, session=self._session)
        self._session.add_all(q)
        return q

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
                subself.session = self.session

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

            @classmethod
            def provider(cls, func):
                def output_func(self, session, **kwargs):
                    cls_instance = cls.get_or_create(session, **kwargs)
                    return func(self, session, cls_instance)
                return output_func

            def get(subself, id):
                inst = subself.query().filter_by(id=id).one()
                return inst

            def delete(subself):
                self.session.delete(subself)
                self.session.commit()
        return Base

    # Engine related things.
    def create_all(self):
        self.require_engine()
        self.Base.metadata.create_all(self.engine)

    def require_engine(self):
        if self.engine is None:
            logging.critical("No database found. Run `umptag init` first.")
            exit(1)


db = DBHandler(find_database())


def create_database():
    if db.db_loc is None:
        db.bind('.umptag.db')
        db.create_all()
        db.session.commit()
        print("Database initialized in {}.".format(os.path.abspath(db.db_loc)))
        exit(0)
    else:
        print("Database already exists in {}.".format(db.db_loc))
        exit(1)


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
