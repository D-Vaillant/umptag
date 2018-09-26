from sqlalchemy import create_engine
from models import File, Tag, initialize_tables


class DatabaseHandler():
    """ An interface to the database. """
    def __init__(self, db_name):
        from models import MetaData as meta
        self.meta = meta
        DB_URI = "sqlite:///"
        engine = create_engine(DB_URI + '%s.db' % db_name)
        self.meta = meta
        self.meta.reflect(bind=engine)

    def add_file(self, file_name):
        self.files.insert().values(filename=file_name)

    def rm_file(self, file_name):
        self.files.delete().where(self.files.c.filename == file_name)

    def tag_file(self, file_name, value, key='', poly=False):
        file = self.get_file(file_name)
        if poly:
            file.append_tag(key=key, value=value)
        else:
            file[key] = value

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


def create_database(*args):
    initialize_tables( *args)