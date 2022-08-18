#!usr/bin/env python

import glob
import wallpaperSorterVariables as gv

def getPdfGlob(dueDate, material, fullOrSamp): # Takes a "due date" (OT, Late, Today, Future), a material type, and full or sample, then returns a glob list 
    dueDateLookup = {
        'OT':'1 - OT Orders/',
        'Late':'2 - Late/',
        'Today':'3 - Today/',
        'Future':'4 - Future/',
    }
    material = gv.dirLookupDict[material]
    if fullOrSamp.lower() == 'full':
        fullOrSamp = 'Full/**/*.pdf'
    else:
        fullOrSamp = 'Sample/*.pdf'
    
    return glob.glob(gv.sortingDir + dueDateLookup[dueDate] + material + fullOrSamp, recursive=True)


