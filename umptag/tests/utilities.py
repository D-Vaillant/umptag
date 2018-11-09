""" utilities.py
Provides testing utilities. """
from random import randint, choice
import os
import string


chars = string.ascii_letters + string.digits


def make_random_word(a=4, b=8):
    return ''.join([choice(chars) for _ in range(randint(a, b))])


def get_random_hierarchy(structure=((2, 2), (lambda: randint(1, 4), 1), (3, 0))):
    """ Takes a list of pairs"""
    all_files = []
    all_dirs = []
    dir_hier = []
    for (file_count, dir_count) in structure:
        if dir_hier == []:
            # This lets us input callables (i.e. random functions).
            try:
                file_count = file_count()
            except TypeError:
                pass
            try:
                dir_count = dir_count()
            except TypeError:
                pass
            all_files += [make_random_word() for f in range(file_count)]
            first_dir_level = [make_random_word() for f in range(dir_count)]
            dir_hier.append(first_dir_level)
            all_dirs += first_dir_level
        else:
            try:
                file_count = file_count()
            except TypeError:
                pass
            try:
                dir_count = dir_count()
            except TypeError:
                pass
            for file in range(file_count):
                parent_dir = os.path.join(*(choice(dir_grp) for dir_grp in dir_hier))
                all_files.append(os.path.join(parent_dir, make_random_word()))
            next_dir_level = [make_random_word() for _ in range(dir_count)]
            # for dir in range(dir_count):
                # dir_name = make_random_word()
                # next_dir_level += make_random_word()
                # next_dirs.append(os.path.join(parent_dir, make_random_word(), ''))
            for dir in next_dir_level:
                parent_dir = os.path.join(*[choice(dir_grp) for dir_grp in dir_hier])
                all_dirs.append(os.path.join(parent_dir, dir, ''))
            dir_hier.append(next_dir_level)
    return (all_files, all_dirs)

