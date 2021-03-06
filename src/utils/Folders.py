import os
import pathlib
import shutil
from .Errors import Errors


def write_string_to_pathfile(string, filepath):
    """
    Write a string to a path file
    :param string: string to write
    :param path: path where write
    """
    try:
        create_directory_from_fullpath(filepath)
        file = open(filepath, 'w+')
        file.write(str(string))
        return 1
    except:
        raise ValueError("Cannot write into folder")

def create_directory_from_fullpath(fullpath):
    """
    Create directory from a fullpath if it not exists.
    """
    directory = os.path.dirname(fullpath)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def create_file_from_fullpath(fullpath):
    """
    Create file from a fullpath if it not exists.
    """
    # TODO (@gabvaztor) Check errors
    if not os.path.exists(fullpath):  # To create file
        file = open(fullpath, 'w+')
        file.close()

def file_exists_in_path_or_create_path(filepath):
    """
    Check if filepath exists and, if not, it creates the dir
    :param filepath: the path to check
    :return True if exists filepath, False otherwise
    """
    try:
        create_directory_from_fullpath(filepath)
        if os.path.exists(filepath):
            return True
        else:
            return False
    except:
        raise ValueError(Errors.check_dir_exists_and_create)

def get_directory_from_filepath(filepath):
    return os.path.dirname(filepath)

def get_filename_from_filepath(filepath):
    return os.path.basename(filepath)

def copy_entire_directory_to_path(path_to_be_copied, path_to_be_paste):

    # Create path
    pathlib.Path(path_to_be_paste).mkdir(parents=True, exist_ok=True)
    copytree(src=path_to_be_copied, dst=path_to_be_paste)

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
