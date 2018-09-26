from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, mapper, relationship
from sqlalchemy.ext.declarative import declared_attr

DB_URI = "sqlite:///"

name = 'foobar'
#engine = create_engine(DB_URI + '%s.db' % name)
meta = MetaData()
meta.reflect(bind=engine)
Session = sessionmaker(bind=engine, autoflush=True)


class QueryMixin:
    @classmethod
    def query(cls):
        return Session().query(cls)


class File(QueryMixin):
    def __init__(self, filename):
        self.filename = filename

    # @declared_attr
    def __getitem__(self, item):
        results = self.tags.filter_by(key=item).all()
        if results:
            return results
        else:
            return ''

    # @declared_attr
    def __setitem__(self, item, value):
        self.tags[:] = [Tag.create_or_get(value=value, key=item)]

    # NOTE this might break because of stupid things
    def append_tag(self, value, key):
        self.tags.append(Tag.create_or_get(value=value, key=key))


class Tag(QueryMixin):
    def __init__(self, value, key=''):
        self.value = value
        self.key = key

    def create_or_get(self, value, key=''):
        q = self.query().filter_by(value=value, key=key).one_or_none()
        if q is None:
            return self.__init__(value, key=key)
        else:
            return q

