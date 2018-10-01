import cmd
import argparse
import functools
from glob import glob
import config
import os.path
from database import create_database, get_database_handle
from pathlib import Path

parser = argparse.ArgumentParser(prog="Tagger", description="Manages tagged files.")
subparsers = parser.add_subparsers(help='subparsers help', dest='command')


def database_cognant(func, *args):
    db = find_database()
    return functools.partial(func, get_database_handle(db))


def find_database():
    cur = os.path.abspath(os.path.curdir)
    db = os.path.join(cur, '.umptag.db')
    if os.path.exists(db):
        return db
    cur, child = os.path.filedir(cur), cur  # go up the hierarchy
    while cur != child:  # because the parent dir of '/' is '/'
        db = os.path.join(cur, '.umptag.db')
        if os.path.exists(db):
            return db
        cur, child = os.path.filedir(cur), cur  # go up the hierarchy
    raise Exception("No database found.")


def collect_files(values):
    # Our weird way of using file extensions.
    if ',' in values and ' ' not in values:
        values = values.split(',')
        values = ['**/*.'+value for value in values]
    outputs = []
    for value in values:
        outputs += glob(value, recursive=True)
    return outputs


def do_init(namespace):
    name = ''.join(namespace.split('.')[:-1])
    config.name = name
    files = collect_files(namespace.files)
    create_database(files)


@database_cognant
def do_add(db, namespace):
    files = collect_files(namespace.files)
    for file in files:
        db.add_file(file)


@database_cognant
def do_rm(db, namespace):
    files = collect_files(namespace.files)
    for file in files:
        db.rm_file(file)


@database_cognant
def do_info(db, namespace):
    most_tagged = max(db.files, key=lambda file: len(file.tags))
    needs_tags = [file for file in db.files if file.tags == []]
    all_keys = set(tag.key for tag in db.tags if tag.key)
    all_values = set(tag.value for tag in db.tags)


@database_cognant
def do_ls(db, namespace):
    for file in db.files:
        print(file)


@database_cognant
def do_show(db, namespace):
    if namespace.file is None:
        exit(3)
    file_row = db.files.filter_by(filename=namespace.file).one()
    print(file_row)


init = subparsers.add_parser('init', help='initializes the folder as tag-aware', action=do_init)
init.add_argument('--name', metavar='[name]', nargs='?', help='Name of the database.',
                  default='foobar')
init.add_argument('files', metavar='files', nargs='*')
init.set_defaults(func=do_init)

add = subparsers.add_parser('add', help='adds files to the database')
add.add_argument('files', metavar='files', nargs='*')
add.set_defaults(func=do_add)

rm = subparsers.add_parser('rm', help='removes files from the database')
rm.add_argument('files', metavar='files', nargs='*')
rm.set_defaults(func=do_rm)

show = subparsers.add_parsers('show', help='displays tag information about a file')
show.add_argument('file', metavar='file', nargs='?')
show.set_defaults(func=do_show)

info = subparsers.add_parser('info', help='prints off information about the database')
info.set_defaults(func=do_info)

ls = subparsers.add_parser('ls', help='lists all tagged files')
ls.set_defaults(func=do_ls)

class TagCmd(cmd.Cmd):
    prompt = '(pytag)'
