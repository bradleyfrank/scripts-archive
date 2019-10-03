#!/usr/bin/env python

__author__ = "Brad Frank"
__email__ = "bradley.frank@gmail.com"
__date__ = "12 April 2014"
__version__ = "0.1"

import difflib
import os
import re


EXT_REGEX = "(\.[^.]+)$"
MOVIES = "Movies"
TV_SHOWS = "TV_Shows"
VALID_EXTS = ["mkv", "mp4", "avi", "ts", "m4v"]


def index_media(directory):
    """
    """

    index = { "shows": [], "invalid": [], "episodes": [] }
    current_dir = ""

    for root, dirs, files in os.walk(directory):
        #
        # path (list): current parent directories
        #
        path = root.split("/")
        depth = len(path)

        #
        # List of directories under the expected depth
        #
        if depth > 3:
            index["invalid"].append(path[1] + "/" + path[2] + "/" + path[3])

        #
        # Keeps a unique list of all shows found
        #
        if depth > 1:
            if path[1] != current_dir:
                index["shows"].append(path[1])
                current_dir = path[1]

        #
        # Alphabetized list of files in current directory
        #
        index["episodes"] += files

    #
    # Alphabetize show list
    #
    index["shows"].sort()

    return index


def invalid_dirs(invalid_dirs):
    """
    """

    print ("")
    print ("========================================================")
    print ("Folders appearing under TV show seasons")
    print ("--------------------------------------------------------")

    #
    # Remove any duplicates from the list
    #
    for directory in set(invalid_dirs):
        print directory

    print ("")


def duplicate_shows(shows):
    """
    """

    print ("")
    print ("========================================================")
    print ("Potential duplicate shows")
    print ("--------------------------------------------------------")

    for show in shows:
        fuzzy_matches = difflib.get_close_matches(show, shows, cutoff=0.8)
        matches = [x for x in fuzzy_matches if x != show]

        if len(matches) > 0:
            print show + ": " + ", ".join(matches)

    print ("")


def duplicate_episodes(episodes):
    """
    """

    print ("")
    print ("========================================================")
    print ("Duplicate episodes")
    print ("--------------------------------------------------------")

    extSearch = re.compile(EXT_REGEX)

    for episode in episodes:
        matches = extSearch.findall(episode)
        print (matches[0])



index = index_media(MOVIES)
invalid_dirs(index["invalid"])
duplicate_shows(index["shows"])
#duplicate_episodes(index["episodes"])