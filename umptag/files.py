import os

def collect_files(root_dir=os.curdir):
    # This is probably just going to wrap os.walk.
    os.walk(root_dir)
