import os.path
import functools
from typing import Union
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, File, Tag, Key


def find_database() -> str:
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
    return '.umptag.db'
    # raise Exception("No database found.")


DB_URI = "sqlite:///"
engine = create_engine(DB_URI + find_database())
Session = sessionmaker(bind=engine)


def database_cognant(func, *args) -> functools.partial:
    return functools.partial(func, get_database_handle(Session()))


class DatabaseHandler():
    """ An interface to the database. """
    def __init__(self, session: Session):
        Base.metadata.reflect(bind=engine)
        self.session = session

    def get_file(self, filename: str) -> Union[File, None]:
        """ Returns a File object or None. """
        filepath = os.path.split(os.path.abspath(filename))
        directory, name = filepath[:-1], filepath[-1]
        q = self.session.query(File).filter_by(directory=directory, name=name)
        return q.first() if q else File(directory=directory, name=name)

    def get_tag(self, value: str, key='') -> Union[Tag, None]:
        """ Returns a Tag object or None. """
        q = self.session.query(Tag).filter_by(value=value, key=key)
        return q.first() if q else Tag(value=value, key=key)

    def add_file(self, filename: str) -> None:
        file = self.get_file(filename)
        file.update_time()
        self.session.merge(file)
        self.session.commit()
        # self.files.insert().values(filename=file_name)

    def rm_file(self, filename: str) -> None:
        file = self.get_file(filename)
        self.session.delete(file)
        self.session.commit()
        # self.files.delete().where(self.files.c.filename == file_name)

    def tag_file(self, filename: str, value: str, key='', poly=False) -> None:
        file = self.get_file(filename)
        tag = self.get_tag(value, key)
        if key == '' or poly:
            file.append_tag(tag)
        else:
            file[key] = value
        self.session.merge(file)
        self.session.commit()

    def untag_file(self, filename: str, value: str, key=''):
        file = self.get_file(filename)
        tag = self.get_tag(value=value, key=key)
        if tag in file.tags:
            file.tags.remove(tag)
            if not tag.files:
                self.session.delete(tag)
            self.session.commit()


    @property
    def files(self):
        """ Returns a list of Files. """
        return self.session.query(File)
        # return self.meta.tables['files']

    @property
    def tags(self):
        """ Returns a list of Tags. """
        return self.session.query(Tag)
        # return self.meta.tables['addresses']


def get_database_handle(session, *args):
    return DatabaseHandler(session)


def create_database(files):
    engine = create_engine(DB_URI + '.umptag.db')
    Base.metadata.create_all(engine)
    sess = Session()
    sess.merge(Key(id=0, name=''))
    sess.commit()
