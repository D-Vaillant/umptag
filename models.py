import datetime
from typing import List
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, UniqueConstraint, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, mapper, relationship
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.associationproxy import association_proxy


Base = declarative_base()
#engine = create_engine(DB_URI + '%s.db' % name)
# Session = sessionmaker(bind=engine, autoflush=True)



class File(Base):
    __tablename__ = "file"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, nullable=False)
    directory = Column('directory', String, nullable=False)
    mod_time = Column(DateTime)
    size = Column('size', Integer, nullable=False)
    is_dir = Column('is_dir', Boolean, nullable=False)

    tags = relationship('Tag', secondary=file_tag, back_populates='file')

    def __init__(self, directory, name, **kwargs):
        filepath = os.path.join(directory, name)
        stat = os.stat(filepath)
        Base.__init__(self,
                directory=directory,
                name=name,
                size=stat.st_size,
                mod_time=stat.st_mtime,
                is_dir=os.path.isdir(filepath)
                **kwargs)

    def append_tag(self, tag):
        self.tags.append(tag)

    def rm_tag(self, value, key=''):
        tag = Tag(value=value, key=key)
        self.tags.remove(tag)

    def update_tag(self):
        self.mod_time = os.stat(self.f_path).st_mtime

    @property
    def f_path(self):
        return os.path.join(directory, name)

    def __str__(self):
        return "{}     ".format(self.filepath)+'  '.join(str(t) for t in self.tags)


class Tag(Base):
    __tablename__ = "tag"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, nullable=False)

    files = relationship('File', secondary=file_tag, back_populates='tag')
    key_id = Column(Integer, ForeignKey('key.id'))
    k = relationship('Key', back_populates='tag')
    key = association_proxy('k', 'name')

    def __init__(self, key='', **kwargs):
        Base.__init__(self, key=key, **kwargs)

    def __str__(self):
        out = self.key+'=' if self.key else ''
        return out+self.name


class Key(Base):
    __tablename__ = "key"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, nullable=False, unique=True)
    v = relationship('Tag', back_populates='key')
    values = association_proxy('v', 'name')

    def __str__(self):
        return self.name

file_tag = Table("file_tag", Base.metadata,
        Column('file_id', ForeignKey('file.id'), primary_key=True),
        Column('tag_id', ForeignKey('tag.id'), primary_key=True))

