#!/usr/bin/python3

# Merge two json tiddler files based on an arbitrary key field
# For use with the AAB TiddlyWiki plugin for Traveller
#
# See:  https://github.com/nickgark/AAB
#       https://tiddlywiki.com/ 

import json
import sys
import argparse

parser = argparse.ArgumentParser(description="Merge two json files full of tiddlers")
parser.add_argument("-k", "--key", help="Key field on which to merge tiddlers")
parser.add_argument("primary", help="Primary json tiddler file")
parser.add_argument("secondary", help="Additional json tiddler file containing fields which will be added to (or override) fields in the primary file")
parser.set_defaults(key="title")

args = parser.parse_args()

prifile = open(args.primary, 'r')
addfile = open(args.secondary, 'r')

pritids = json.load(prifile)
addtids = json.load(addfile)

# Output object

outtids = []

# Build index for additional file

index = {}

for tiddler in addtids:
    title = tiddler[args.key]
    index[title] = tiddler

# Iterate over primary file

for tiddler in pritids:
    title = tiddler[args.key]
    newtid = tiddler.copy()
    if title in index:
        newtid.update(index[title])
    outtids.append(newtid)

print(json.dumps(outtids, indent=4))