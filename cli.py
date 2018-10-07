import cmd
import argparse
import functools
from glob import glob
import config
import os.path
from database import database_cognant, create_database
import models
import pathlib


# Utility function
def collect_files(values):
    # Our weird way of using file extensions.
    if ',' in values and ' ' not in values:
        values = values.split(',')
        values = ['**/*.'+value for value in values]
    outputs = []
    for value in values:
        outputs += glob(value, recursive=True)
    return outputs


def split_filepath(filepath):
    filepath = os.path.abspath(filepath)
    return os.path.dirname(filepath), os.path.basename(filepath)


# The functions invoked by the CLI
def do_init(namespace):
    create_database()


@database_cognant
def do_add(db, namespace):
    files = collect_files(namespace.files)
    for file in files:
        dir, stem = split_filepath(file)
        f = db.File.get_or_create(directory=dir, name=stem)
        db.session.add(f)
    db.session.commit()


@database_cognant
def do_rm(db, namespace):
    files = collect_files(namespace.files)
    for file in files:
        dir, stem = split_filepath(file)
        f = db.File.get_or_create(directory=dir, name=stem)
        if f in File.query:
            db.session.delete(f)
    db.session.commit()


@database_cognant
def do_tag(db, namespace):
    dir, stem = split_filepath(namespace.file)
    f = db.File.get_or_create(directory=dir, name=stem)
    tags = []
    for tag in namespace.tags:
        print("Doing a thing here")
        try:
            k, v = tag.split('=')
        except ValueError:
            k, v = '', tag
        t = db.Tag.get_or_create(value=v, key=k)
        f.tags.append(t)
        tags.append(t)
    db.session.commit()
    print(f"Tagged {stem} with {', '.join(str(tag) for tag in tags)}.")


@database_cognant
def do_untag(db, namespace):
    dir, stem = split_filepath(namespace.file)
    f = db.File.get_or_create(directory=dir, name=stem)
    tags = []
    for tag in namespace.tags:
        print("Doing a thing here")
        try:
            k, v = tag.split('=')
        except ValueError:
            k, v = '', tag
        t = db.Tag.get_or_create(value=v, key=k)
        if t in f.tags:
            f.tags.remove(t)
            tags.append(t)
    print(db.session.dirty)
    print(db.session.new)
    db.session.commit()
    print(f"Removed tags from {f.name}: {', '.join(str(tag) for tag in tags)}.")


@database_cognant
def do_merge(db, namespace):
    # Merge two tags!
    pass

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
    file = db.get_file(namespace.file)
    if file is None:
        exit(2)
    print(file)


"""
    tmsu init
    tmsu info
        Shows where the database is.
    tmsu repair
        Detects move or modified.

    tmsu tag filename tag tag key=value
         tag --tags "tag tag tag" filename filename filename
      Prints when a new tag is created.

    tmsu merge tag_to_merge destination_tag

    tmsu tags filename
        linebroken
    tmsu tags filename filename
        filename1: tag tag tag
        filename2: tag tag tag

    tmsu files tag1 tag2
        linebroken files with tag
    tmsu files tag_predicate
        Include "and", "or", parentheses, negation

"""
parser = argparse.ArgumentParser(prog="Tagger", description="Manages tagged files.")
subparsers = parser.add_subparsers(help='subparsers help', dest='command')

init = subparsers.add_parser('init', help='initializes the folder as tag-aware')
init.set_defaults(func=do_init)

# Manipulate files.
add = subparsers.add_parser('add', help='adds files to the database')
add.add_argument('files', metavar='files', nargs='*')
add.set_defaults(func=do_add)

rm = subparsers.add_parser('rm', help='removes files from the database')
rm.add_argument('files', metavar='files', nargs='*')
rm.set_defaults(func=do_rm)

# Manipulate tags.
tag_ = subparsers.add_parser('tag', help='tag a file')
tag_.add_argument('file', metavar='filepath', nargs='?')
tag_.add_argument('tags', metavar='tag (tag...)', nargs='*')
tag_.set_defaults(func=do_tag)

untag_ = subparsers.add_parser('untag', help='tag a file')
untag_.add_argument('file', metavar='filepath', nargs='?')
untag_.add_argument('tags', metavar='tag', nargs='*')
untag_.set_defaults(func=do_untag)

merge_tag = subparsers.add_parser('merge', help='merge a tag with another tag')
merge_tag.add_argument('tag', metavar='tag', nargs='?')
merge_tag.add_argument('merged', metavar='tag_to_merge', nargs='?')
merge_tag.set_defaults(func=do_merge)

# Display information.
show = subparsers.add_parser('tags', help='displays tag information about a file')
show.add_argument('file', metavar='file', nargs='?')
show.set_defaults(func=do_show)

info = subparsers.add_parser('info', help='prints off information about the database')
info.set_defaults(func=do_info)

ls = subparsers.add_parser('ls', help='lists all tagged files')
ls.set_defaults(func=do_ls)


class TagCmd(cmd.Cmd):
    prompt = '(pytag)'

if __name__ == "__main__":
    args = parser.parse_args()
    args.func(args)

