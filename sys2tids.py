#!/usr/bin/python3

# Generate system tiddlers from TravellerMap 
# for use with the AAB TiddlyWiki plugin for Traveller
#
# See:  https://github.com/nickgark/AAB
#       https://tiddlywiki.com/
#       https://travellermap.com/  

import json
import sys
import csv
import re
import io
from collections import OrderedDict
import argparse
import requests

def main():

    parser = argparse.ArgumentParser(description="Generate system tiddlers")
    parser.add_argument("-a", "--all", help="Generate system tiddlers for all sectors", action="store_true")
    parser.add_argument("-r", "--routes", help="Generate route information for systems", action="store_true")
    parser.add_argument("-s", "--sector", help="Generate tiddlers for sectors and subsectors", action="store_true")
    parser.add_argument("-m", "--milieu", help="Milieu for system data",
                        choices=["M0","M990","M1105","M1120",
                                 "M1201","M1248","M1900"],
                        default="M1105")
    parser.add_argument("sectors", nargs="*", help="Sectors for which system tiddlers are to be generated")
    args = parser.parse_args()

    sophontdict = get_sophonts()
    sectordict = get_sectors()

    worlds = []

    if args.all:
        sectors = list(sectordict.keys())
    else:
        sectors = args.sectors

    # iterate over the requested sectors
    for sector in sectors:
        secworlds = get_systems(sector, args.milieu, sophontdict, sectordict)
        
        metadata = get_metadata(sector, args.milieu)
    
        if args.sector:
            worlds.extend(get_sector(metadata))
    
        if args.routes:
            secworlds = merge(secworlds, get_routes(metadata), 'hex')
        
        worlds.extend(secworlds)
    
    print(json.dumps(tidy(worlds), indent=4))

def get_sector(metadata):
    
    data = []
    
    sector = {}
    # currently gets the first name (there may be multiple) on
    # the grounds that's the name used by the 3I
    # handling of names used by other polities is future work    
    sector['title'] = metadata['Names'][0]['Text']
    sector['sx'] = str(metadata['X'])
    sector['sy'] = str(metadata['Y'])
    sector['tags'] = "Sector"
    
    data.append(sector)
    
    for sub in metadata['Subsectors']:
        subsector = {}
        subsector['sector'] = sector['title']
        subsector['subsector'] = sub['Index']
        subsector['name'] = sub['Name']
        subsector['title'] = subsector['name'] + "/" + subsector['sector']
        subsector['tags'] = "Subsector"
        
        data.append(subsector)
    
    return data

def get_routes(metadata):
    worlds = []

    hexes = {}
    
    routes = metadata['Routes']
    
    # code below needs to do something about routes whose starts/ends
    # lie outside the current sector
    for route in routes:
        sx = int(route['Start'][0:2])
        sy = int(route['Start'][2:4])
        ex = int(route['End'][0:2])
        ey = int(route['End'][2:4])
        
        if ('StartOffsetX' in route):
            sx = sx + (32*int(route['StartOffsetX']))
            sx = 0 if (sx < 0) else sx
        
        if ('StartOffsetY' in route):
            sy = sy + (40*int(route['StartOffsetY']))
            sy = 0 if (sy < 0) else sy
        
        if ('EndOffsetX' in route):
            ex = ex + (32*int(route['EndOffsetX']))
            ex = 0 if (ex < 0) else ex
        
        if ('EndOffsetY' in route):
            ey = ey + (40*int(route['EndOffsetY']))
            ey = 0 if (ey < 0) else ey
          
        
        start = str(sx).zfill(2) + str(sy).zfill(2)
        end = str(ex).zfill(2) + str(ey).zfill(2)

        
        if start not in hexes:
            hexes[start] = set()
        if end not in hexes:
            hexes[end] = set()
            
        hexes[start].add(end)
        hexes[end].add(start)
    
    for hex in hexes:
        world = {}
        world['hex'] = hex
        world['routes'] = " ".join(hexes[hex])
        worlds.append(world)
        
    return worlds

def get_systems(sector, milieu, sophontdict, sectordict):
    worlds = []
    
    # fetch the world data for the sector
    sectab = requests.get("https://travellermap.com/data/" + sector + 
                          "/tab?milieu=" + milieu).text
    
    reader = csv.DictReader(io.StringIO(sectab), delimiter='\t')
    
    # iterate over the worlds in the sector
    for row in reader:
        worlds.append(parse_system(row, sophontdict, sectordict))
    
    return worlds

def get_metadata(sector, milieu):
    return json.loads(requests.get("https://travellermap.com/api/metadata?sector=" + sector + "&milieu=" + milieu).text)

def merge(pritids, addtids, key):

    result = []

    # Build index for additional file
    index = {}

    for tiddler in addtids:
        index[tiddler[key]] = tiddler

    # Iterate over primary file

    for tiddler in pritids:
        newtid = tiddler.copy()
        if tiddler[key] in index:
            newtid.update(index[tiddler[key]])
        result.append(newtid)

    return result

def tidy(worlds):
    
    order = ['title', 'name', 'text',
        'sector', 'subsector', 'hex', 'hx', 'hy','sx','sy',
        'starport',
        'diameter',
        'atmosphere', 'atmoscomp',  
        'hydrographics', 'hydrocomp',
        'population', 'popmult', 'demographics', 'homeworld',
        'government', 'ownersector', 'ownerhex', 'corporation', 'client',
        'lawlevel',
        'techlevel',
        'zone', 'bases', 'tradecodes',
        'importance',
        'resources', 'labour', 'infrastructure', 'efficiency',
        'heterogeneity', 'acceptance', 'strangeness', 'symbols',
        'stars', 'worlds', 'belts', 'gasgiants',
        'allegiance',
        'routes',
        'tags']

    return [OrderedDict(sorted(world.items(), 
                               key=lambda p: order.index(p[0])))
            for world in worlds]

def parse_system(row, sophonts, sectors):
    tenths = {
        "0": "(< 10%)",
        "1": "(10%)",
        "2": "(20%)",
        "3": "(30%)",
        "4": "(40%)",
        "5": "(50%)",
        "6": "(60%)",
        "7": "(70%)",
        "8": "(80%)",
        "9": "(90%)",
        "W": "World"	
    }

    hwracere = re.compile(r"(Di)?[(\[]([^)\]]+)[)\]]([0-9W]?)")
    racere = re.compile(r"([A-Za-z']{3,4})([0-9W])")
    ownerre = re.compile(r"O:(([A-Za-z]{3,4})-)?(\d{4})")
    importre = re.compile(r"\{\s*(-?\d)\s*\}")
    economre = re.compile(r"\((\S)(\S)(\S)([+-]\S)\)")
    culturre = re.compile(r"\[(\S)(\S)(\S)(\S)\]")

    world = {}
    tradecodes = []
    demographics = []
    homeworld = []
    
    world['tags'] = "System"
    world['title'] = row['Name']
    if row['Name'] != "":
        world['title'] += ' '
    world['title'] += '(' + sectors[row['Sector']] + ' ' + row['Hex'] + ')'
    world['name'] = row['Name']
    world['sector'] = sectors[row['Sector']]
    world['subsector'] = row['SS']
    world['hex'] = row['Hex']
    world['hx'] = row['Hex'][0:2]
    world['hy'] = row['Hex'][2:4]
    
    world['starport'] = row['UWP'][0]
    world['diameter'] = row['UWP'][1]
    world['atmosphere'] = row['UWP'][2]
    world['hydrographics'] = row['UWP'][3]
    world['population'] = row['UWP'][4]
    world['government'] = row['UWP'][5]
    world['lawlevel'] = row['UWP'][6]
    world['techlevel'] = row['UWP'][8]

    world['zone'] = row['Zone']
    
    world['bases'] = " ".join(list(row['Bases']))
        
    world['popmult'] = row['PBG'][0]
    world['belts'] = row['PBG'][1]
    world['gasgiants'] = row['PBG'][2]
    
    ix = importre.match(row['{Ix}'])
    if (ix != None):
        world['importance'] = ix.group(1)
    
    ex = economre.match(row['(Ex)'])
    if (ex != None):
        world['resources'] = ex.group(1)
        world['labour'] = ex.group(2)
        world['infrastructure'] = ex.group(3)
        world['efficiency'] = ex.group(4)
    
    cx = culturre.match(row['[Cx]'])
    if (cx != None):
        world['heterogeneity'] = cx.group(1)
        world['acceptance'] = cx.group(2)
        world['strangeness'] = cx.group(3)
        world['symbols'] = cx.group(4)
    
    world['stars'] = row['Stars']
    
    world['worlds'] = row['W']
    world['allegiance'] = row['Allegiance']

    world['worlds'] = row['W']
    world['allegiance'] = row['Allegiance']
    
    # Match homeworld races
    for match in hwracere.finditer(row['Remarks']):
        if match.group(2) == "minor":
            sophont = "Minor Race"
        elif match.group(2) == "Hminor":
            sophont = "Human Minor Race"
        else:
            sophont = match.group(2)
            
        if match.group(1) == "Di":
            homeworld.append("[[%s (extinct)|%s]]" % (sophont, sophont))
            tradecodes.append("Di")
        else:
            if match.group(3) != "":
                homeworld.append("[[%s]]" % (sophont))
                demographics.append("[[%s %s|%s]]" % (sophont, tenths[match.group(3)], sophont))
            else:
                homeworld.append("[[%s]]" % (sophont))
                demographics.append("[[%s World|%s]]" % (sophont, sophont))
  
    # Match races
    for match in racere.finditer(row['Remarks']):
        if match.group(1) in sophonts:
            sophont = sophonts[match.group(1)]
            demographics.append("[[%s %s|%s]]" % (sophont, tenths[match.group(2)], sophont))
 
    if len(homeworld) > 0:
        world['homeworld'] = "<br/>".join(homeworld)
        
    if len(demographics) > 0:
        world['demographics'] = "<br/>".join(demographics)
  
    # Match owners
    for match in ownerre.finditer(row['Remarks']):
        if match.group(1):
            if match.group(2) in sectors:
                world['ownersector'] = sectors[match.group(2)]

        else:
            world['ownersector'] = sectors[row['Sector']]

        world['ownerhex'] = match.group(3)
        
    for code in row['Remarks'].split():
        if len(code) <= 3:
            tradecodes.append(code)
        
    world['tradecodes'] = " ".join(tradecodes)
 
    return world
        
def get_sophonts():
    """Fetch sophonts from travellermap and return a dictionary of abbreviations
    
    See https://travellermap.com/doc/api for further details
    """
    
    sophs = json.loads(requests.get("https://travellermap.com/t5ss/sophonts").text)
    
    sophonts = {}
    
    for soph in sophs:
        sophonts[soph['Code']] = soph['Name']
        
    return sophonts
    
def get_sectors():
    """Fetch sectors from travellermap and return a dictionary of abbreviations
    
    Currently defaults to official M1105 data
    See https://travellermap.com/doc/api for further details
    """
    
    secs = json.loads(requests.get("https://travellermap.com/api/universe?era=M1105&tag=OTU&requireData=1").text)

    sectors = {}

    for sec in secs['Sectors']:
        sectors[sec['Abbreviation']] = sec['Names'][0]['Text']
    
    return sectors

if __name__ == "__main__":
    main()


