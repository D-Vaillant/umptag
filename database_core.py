from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm mapper, relationship
import config
DB_URI = "sqlite:///"
engine = create_engine(DB_URI + '%s.db' % config.name)


def initialize_tables(name, *args):
    meta = MetaData(bind=engine)
    _tag_table = Table('tags', meta,
                       Column('id', Integer, primary_key=True),
                       Column('key', String, default=''),
                       Column('value', String, nullable=False)
                       )

    _file_table = Table('files', meta,
                        Column('id', Integer, primary_key=True),
                        Column('filepath', String, nullable=False),
                        )

    _file_tag_junction = Table('file_tags', meta,
                               Column('file_id', ForeignKey('files.id'), primary_key=True),
                               Column('tag_id', ForeignKey('tags.id'), primary_key=True))

    mapper(File, _file_table,
           properties={'tags': relationship(Tag, secondary=_file_tag_junction,
                                            back_populates=_file_table,
                                            cascade="all, delete-orphan")})

    mapper(Tag, _tag_table,
           properties={'files': relationship(File, secondary=_file_tag_junction,
                                             back_populates=_tag_table)})
    meta.create_all(bind=engine)