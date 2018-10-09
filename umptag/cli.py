import argparse
from umptag.actions import (do_init,
                            do_add,
                            do_rm,
                            do_tag,
                            do_untag,
                            do_merge,
                            do_info,
                            do_ls,
                            do_show,
                            do_clean
                            )


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
parser = argparse.ArgumentParser(prog="umptag", description="Manages tagged files.")
parser.set_defaults(func=lambda _: parser.print_help())
subparsers = parser.add_subparsers(help='subparsers help', dest='command')

init = subparsers.add_parser('init', help='initializes the folder as tag-aware')
init.set_defaults(func=do_init)

"""
# Manipulate files.
add = subparsers.add_parser('add', help='adds files to the database')
add.add_argument('files', metavar='files', nargs='*')
add.set_defaults(func=do_add)

rm = subparsers.add_parser('rm', help='removes files from the database')
rm.add_argument('files', metavar='files', nargs='*')
rm.set_defaults(func=do_rm)
"""

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

show = subparsers.add_parser('show', help='')
ls.set_defaults(func=do_show)

clean = subparsers.add_parser('clean', help='cleans superfluous files')
clean.add_argument('confirm', action='store_true')
clean.set_defaults(func=do_clean)

def main():
    args = parser.parse_args()
    args.func(args)
    return 0
