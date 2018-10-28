import os
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship


def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw):
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
        cache[key] = obj
        return obj


class UniqueMixin(object):
    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
                    session,
                    cls,
                    cls.unique_hash,
                    cls.unique_filter,
                    cls,
                    arg, kw
               )


Base = declarative_base()


class Tag(UniqueMixin, Base):
    __tablename__ = "tag"
    id = Column('id', Integer, primary_key=True)
    value = Column('value', String, nullable=False)
    key = Column('key', String, default='')
    files = relationship('File', secondary=file_tag, back_populates='tags')

    @classmethod
    def unique_hash(cls, key, value):
        return (key, value)

    @classmethod
    def unique_filter(cls, query, key, value):
        return query.filter_by(key=key, value=value)

    def __str__(self):
        out = self.key+'=' if self.key else ''
        return out+self.value

    def __repr__(self):
        return f"Tag(id={self.id}, value={self.value}, key={self.key}, files=[{', '.join(file.name for file in self.files)}])"


class File(Base):
    __tablename__ = "file"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, nullable=False)
    directory = Column('directory', String, nullable=False)
    size = Column('size', Integer, nullable=False)
    is_dir = Column('is_dir', Boolean, nullable=False)
    mod_time = Column(DateTime)

    tags = relationship('Tag', secondary=file_tag, back_populates='files')

    def __init__(self, **kwargs):
        try:
            directory = kwargs['directory']
            name = kwargs['name']
        except KeyError:
            raise NameError("File did not have a specified name or directory.")
        filepath = os.path.join(directory, name)
        Base.__init__(self,
                directory=directory,
                name=name,
                size=os.stat(filepath).st_size,
                is_dir=os.path.isdir(filepath))
        self.update_time()

    """
    @classmethod
    def fetch(cls, filepath):
        try:
            filepath = os.path.abspath(filepath)
            dir, name = os.path.dirname(filepath), os.path.basename(filepath)
        except TypeError:
            raise FileNotFoundError
        return cls.get_or_create(directory=dir, name=name)
    """
    def __getitem__(self, key) -> str:
        for tag in self.tags:
            if tag.key == key:
                return tag.value
        else:
            # NOTE: Defaultdict, keyerror -> empty.
            return ''

    """
    def __setitem__(self, key, value):
        for tag in self.tags:
            if tag.key == key and tag.value != value:
                self.tags.remove(tag)
                break
        self.tags.add(Tag(key=key, value=value))

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
    """

    def update_time(self):
        self.mod_time = datetime.fromtimestamp(os.stat(self.f_path).st_mtime)

    @classmethod
    def unique_hash(cls, directory, name, **kwargs):
        return os.path.join(directory, name)

    @classmethod
    def unique_filter(cls, query, directory, name, **kwargs):
        return query.filter_by(name=name, directory=directory)

    @property
    def f_path(self):
        return os.path.join(self.directory, self.name)

    def __str__(self):
        return "{}     ".format(self.name)+'  '.join(str(t) for t in self.tags)

file_tag = Table("file_tag", Base.metadata,
        Column('file_id', Integer, ForeignKey('file.id'), primary_key=True),
        Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True))

