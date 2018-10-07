import os
from datetime import datetime
from typing import List
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import db


file_tag = Table("file_tag", db.Base.metadata,
        Column('file_id', Integer, ForeignKey('file.id'), primary_key=True),
        Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True))


class Tag(db.Base):
    __tablename__ = "tag"
    id = Column('id', Integer, primary_key=True)
    value = Column('value', String, nullable=False)
    key = Column('key', String, default='')
    files = relationship('File', secondary=file_tag, back_populates='tags')

    def __str__(self):
        out = self.key+'=' if self.key else ''
        return out+self.value

    def __repr__(self):
        return f"Tag(id={self.id}, value={self.value}, key={self.key}, files=[{', '.join(file.name for file in self.files)}])"


class File(db.Base):
    __tablename__ = "file"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, nullable=False)
    directory = Column('directory', String, nullable=False)
    mod_time = Column(DateTime)
    size = Column('size', Integer, nullable=False)
    is_dir = Column('is_dir', Boolean, nullable=False)

    tags = relationship('Tag', secondary=file_tag, back_populates='files')

    def __init__(self, **kwargs):
        try:
            directory = kwargs['directory']
            name = kwargs['name']
            filepath = os.path.join(directory, name)
        except KeyError:
            raise NameError("File did not have a specified name or directory.")
        stat = os.stat(filepath)
        db.Base.__init__(self,
                directory=directory,
                name=name,
                size=stat.st_size,
                is_dir=os.path.isdir(filepath))
        self.update_time()

    @Tag.provider
    def append_tag(self, session, tag):
        self.tags.append(tag)
        session.commit()

    @Tag.provider
    def rm_tag(self, session, tag):
        self.tags.remove(tag)

    def update_time(self):
        self.mod_time = datetime.fromtimestamp(os.stat(self.f_path).st_mtime)

    @property
    def f_path(self):
        return os.path.join(self.directory, self.name)

    def __str__(self):
        return "{}     ".format(self.name)+'  '.join(str(t) for t in self.tags)
