#!/usr/bin/python3

# Generate sector and subsector tiddlers from TravellerMap 
# for use with the AAB TiddlyWiki plugin for Traveller
#
# See:  https://github.com/nickgark/AAB
#       https://tiddlywiki.com/
#       https://travellermap.com/  

import json
import sys
import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description="Generate sector tiddlers")
    parser.add_argument("-s", "--subsectors", 
                        help="Generate subsector tiddlers", action="store_true")
    args = parser.parse_args()

    # output json
    output = []

    sectors = json.loads(requests.get("https://travellermap.com/api/universe?era=M1105&tag=OTU&requireData=1").text)['Sectors']
    
    for sector in sectors:
        
        tiddler = {}
    
        # currently gets the first name (there may be multiple) on
        # the grounds that's the name used by the 3I
        # handling of names used by other polities is future work    
        tiddler['title'] = sector['Names'][0]['Text']
    
        tiddler['sx'] = sector['X']
        tiddler['sy'] = sector['Y']
        
        tiddler['tags'] = "Sector"
        
        if args.subsectors:
            output.extend(get_subsectors(sector['Abbreviation'], 
                                         sector['Names'][0]['Text']))
    
        output.append(tiddler)
        
    print(json.dumps(output, indent=4))

def get_subsectors(sector, name):
    
    metadata = json.loads(requests.get("https://travellermap.com/api/metadata?sector=" + sector).text)
    
    subsectors = []
    
    for sub in metadata['Subsectors']:
        subsector = {}

        subsector['sector'] = name
        subsector['subsector'] = sub['Index']
        subsector['name'] = sub['Name']
        subsector['title'] = sub['Name'] + "/" + name
        subsector['tags'] = "Subsector"
    
        subsectors.append(subsector)
        
    return subsectors
        
if __name__ == "__main__":
    main()