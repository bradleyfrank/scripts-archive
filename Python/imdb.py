#!/usr/bin/env python

# Query IMDB for movie year and rating from a list of titles.

import collections
import json
import re
import sys
import urllib2

fname = "movies.list"
movies = {}

with open(fname) as f:
    titles = f.readlines()

for title in titles:
    url = "http://www.imdbapi.com/?t=" + '+'.join(title.split())
    request = urllib2.Request(url)
    data = json.load(urllib2.urlopen(request))

    movie = title.rstrip('\n')

    if 'Error' in data:
        movies[movie] = {'found': "No entry found."}
    elif data['Type'] == 'movie':
        movies[data['Title']] = {'found': True,
                                 'rating': data['imdbRating'],
                                 'year': data['Year']}
    else:
        movies[movie] = {'found': "Found \"" + data['Type'] + "\" instead."}

movies = collections.OrderedDict(sorted(movies.items()))

for movie, info in movies.iteritems():
    if info['found'] is True:
        print(movie + " (" + info['year'] + "): " + info['rating'])
    else:
        print(movie + ": " + info['found'])
