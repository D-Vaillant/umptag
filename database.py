from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine


class DatabaseHandler():
    """ An interface to the database. """
    DB_URI = "sqlite:///"

    def __init__(self, name):
        self.engine = create_engine(self.DB_URI + '%s.db' % name)
        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)

    def initialize_tables(self, *args):
        files = Table('files', self.meta,
                      Column('id', Integer, primary_key=True),
                      Column('filepath', String, nullable=False),
                      )
        tags = Table('tags', self.meta,
                     Column('id', Integer, primary_key=True),
                     Column('key', String, default=''),
                     Column('value', String, nullable=False)
                     )
        file_tags = Table('file_tags', self.meta,
                          Column('file_id', ForeignKey('files.id'), primary_key=True),
                          Column('tag_id', ForeignKey('tags.id'), primary_key=True))

    @property
    def files(self):
        """ Returns a list of Files. """
        return self.meta.tables['files']

    @property
    def tags(self):
        """ Returns a list of Tags. """
        return self.meta.tables['addresses']

def get_database_handle(db_name, *args):
    return DatabaseHandler(name=db_name)


def create_database(db_name, *args):
    db = DatabaseHandler(name=db_name)
    db.initialize_tables(*args)