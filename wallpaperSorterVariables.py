#!usr/bin/env python

import os
from datetime import date, datetime
from sqlitedict import SqliteDict

today = datetime.today()

#Location for Caldera's Folders
if os.path.expanduser('~').split('/')[-1] == 'Trevor':
    calderaDir = '/opt/caldera/var/public/'
    driveLocation = '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment'
else:
    calderaDir = '/Volumes/Print Drive/caldera/public/'
    driveLocation = '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Fulfillment'

orderdb = calderaDir + 'z_Storage/z_WallpaperDB/lvdOrderDatabase.sqlite'
ordersDict = SqliteDict(orderdb, autocommit=True)
BatchCounterDB = calderaDir + 'z_Storage/z_WallpaperDB/lvdGlobalBatchCounter.sqlite'
globalBatchCounter = SqliteDict(BatchCounterDB, autocommit=True)
#globalBatchCounter['BatchCounter'] = 1

batchFoldersDir = calderaDir + '2 Batch Folders/'
downloadDir = calderaDir + '3 Downloaded/'
needsAttention = calderaDir + '4 Needs Attention/'
sortingDir = calderaDir + '5 Sorted for Print/'

dirLookupDict = { #Dictionary for dynamically creating a directory path for sorting based on lookup tables
    'Sm':'Smooth/', #Smooth Folders
    'Smooth':'Smooth/',
    'Wv':'Woven/', #Woven Folders
    'Woven':'Woven/',
    'Tr':'Traditional/', #Traditional Folders
    'Full':'Full/', #Full Folders
    'Samp':'Sample/',
    'Sample':'Sample/', #Sample Folders
    'RepeatDict':{
        2:'Repeat 2/', #2 Foot Repeats
        3:'Repeat Non-2/', #Non-2 Foot Repeats
        4:'Repeat Non-2/', #Non-2 Foot Repeats
        5:'Repeat Non-2/', #Non-2 Foot Repeats
        6:'Repeat Non-2/', #Non-2 Foot Repeats
        7:'Repeat Non-2/', #Non-2 Foot Repeats
        8:'Repeat Non-2/', #Non-2 Foot Repeats
        9:'Repeat Non-2/', #Non-2 Foot Repeats
        10:'Repeat Non-2/', #Non-2 Foot Repeats
        11:'Repeat Non-2/', #Non-2 Foot Repeats
        12:'Repeat Non-2/', #Non-2 Foot Repeats 
    },
    1:'Odd Panels/',
    0:'Even Panels/',
    'MaterialLength':{ #this should reflect printable length. Smooth rolls are 150 feet, but we have 148 printable feet on each roll.
        'Smooth' : (150 * 12) - 2,
        'Woven' : (100 * 12) - 2,
        'Traditional' : (100 * 12) - 2,
        'Sm' : (150 * 12) - 2,
        'Wv' : (100 * 12) - 2,
        'Tr' : (100 * 12) - 2,
    },
}

substrate = {
    'Woven Peel and Stick':'Wv',
    'Woven':'Wv',
    'Wv':'Woven',
    'Smooth Peel and Stick':'Sm',
    'Smooth':'Sm',
    'Sm':'Smooth',
    'Traditional':'Tr'
    }

shippingMethods = {
    'Standard':'Stnd',
    'Sample Standard':'SmStnd',
    'International Standard':'InStnd',
    'Priority':'Prty',
    'International Priority':'InPrty',
    'Rush':'Rush',
}

pdfsToRename = {
    
}

countOfRefPdfs = { #Running count of PDFs that are referenced during sample creating. If a PDF is referenced more than once, the order and PDF are printed to alert fulfillment of dual-type samples
    
}

orderItemsDict = {
}

today = date.today()