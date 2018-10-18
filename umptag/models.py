import os
from datetime import datetime
from typing import List
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import db


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

    @classmethod
    def fetch(cls, filepath):
        try:
            filepath = os.path.abspath(filepath)
            dir, name = os.path.dirname(filepath), os.path.basename(filepath)
        except TypeError:
            raise FileNotFoundError
        return cls.get_or_create(directory=dir, name=name)

File['key'] -> Tag or Tags
File['key'] = 'value' -> Remove other key tags, add key=value.
File['key'] += 'value' -> Add key=value.

    def __getitem__(self, key):
        class TagProxy(list):
            def __init__(subself, key, *args, **kwargs):
                subself.key = key
                subself._update_tags()

            @property
            def _get_tags(subself):
                return (tag for tag in self.tags if tag.key == key)

            def _update_tags(subself):
                super().__init__(subself._get_tags)

            def __eq__(subself, value):
                remove = [tag for tag in self.tags if tag.value != value]
                for tag in filter(lambda t: t.value != value, subself._get_tags):
                    self.rm_tag(tag=tag)
                if remove:
                    pass
                else:
                    self.append_tag(tag=tag)
                subself._update_tags()

            def __iadd__(subself, value):
                self.append_tag(key=subself.key, value=value)
                subself._update_tags()
        return TagProxy(key)

    def __setitem__(self, key, value):
        pass


    def append_tag(self, tag=None, key='', value='',
            append=False):
        self.session.add(self)
        if tag is None:
            Tag.get_or_create(key=key, value=value)
        self.tags.append(tag)
        self.session.commit()

    def rm_tag(self, tag=None, key='', value='',
            do_glob=False):
        self.session.add(self)
        if tag is not None:
            tags = [tag]
        elif do_glob:
            # TODO figure out how ilike works properly
            tags = self.session.query(Tag).ilike(key=key, value=value)
        else:
            tags = [self.session.query(Tag).filter_by(key=key, value=value).one_or_none()]

        for tag in tags:
            if tag is None:
                # The specified tag does not exist.
                print("Tag does not exist.")
            else:
                if tag in self.tags:
                    # The tag works; hurray.
                    self.tags.remove(tag)
                    print("Successfully removed the tag.")
                else:
                    print("File not tagged with that.")

    def update_time(self):
        self.session.add(self)
        self.mod_time = datetime.fromtimestamp(os.stat(self.f_path).st_mtime)
        self.session.commit()

    @property
    def f_path(self):
        return os.path.join(self.directory, self.name)

    def __str__(self):
        return "{}     ".format(self.name)+'  '.join(str(t) for t in self.tags)
