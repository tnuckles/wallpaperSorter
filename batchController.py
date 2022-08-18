#!usr/bin/env python

import math
import batchMenu as bMenu
from batchSorting import sortAndCalculateFullLength as bSort
import batchCreate as bCreate

### Global Variables

currentBatchDict = {
        'batchDetails': {
            'ID':'',
            'material':'',
            'priority':0,
            'length':0,
            'materialLength':0,
            'careAboutMinimumLength':True,
        },
        'OT':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Late':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Today':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Future':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
    }

''' Function Definitions '''

'''### Main Controller and Functions ###'''

def buildABatch(): # Begins the batch building process
    print('\n| Welcome to Build-A-Batch!\n')
    
    # Prompts user for batch information and confirms their selection
    batchDetails = bMenu.batchDetailsMenu()
    bMenu.confirmBatchMenu(batchDetails['material'],int(batchDetails['materialLength']/12))
    
    # Resets currentBatchDict, then adds the details from the previous section
    resetCurrentBatchDict()
    currentBatchDict['batchDetails']['ID'] = bMenu.getBatchID()
    currentBatchDict['batchDetails']['material'] = batchDetails['material']
    currentBatchDict['batchDetails']['materialLength'] = batchDetails['materialLength']
    currentBatchDict['batchDetails']['careAboutMinimumLength'] = batchDetails['minimumLength']

    #checks for orders that need to be printed
    '''
    Are there [OT] orders?
    How many [OT] orders are there?
    How many are sample orders?
        How long are they?
        Will the samples take up more than 20% of the total batch length?
            If they will take up less than 30%, add them all to the batch
            Otherwise, only add in enough to take up 20% of the batch.
        Recalculate batch length
    How many are full orders?
        Sort them by length. 
        How long will they be?
            By default, full orders should comprise 80% of the order (unless overriden by the sample logic above)
            If the total length of [OT] orders is less than the remaining length, add them all in.
            Otherwise, add in enough OT orders to meet, but not exceed, the remaining length.
        Recalculate batch length.
    
    Add in reverse order - OT should be added last, then Late, then Today, then Future.
    '''

    otFullGlob = bCreate.getPdfGlob('Late', currentBatchDict['batchDetails']['material'], 'full')
    otSampleGlob= bCreate.getPdfGlob('Late', currentBatchDict['batchDetails']['material'], 'Sample')
    totalOtFullCount = len(otFullGlob)
    totalOtSampleCount = len(otSampleGlob)
    totalOtSampleLength = ((math.floor(totalOtSampleCount / 2) + (totalOtSampleCount % 2)) * 9.5)
    totalOtFullLength = bSort(otFullGlob)
    if (totalOtFullCount + totalOtSampleCount) > 0:
        print('| Full OT Orders:', str(totalOtFullCount))
        print('| Sample OT Orders:', str(totalOtSampleCount))
        print('| Sample OT Length:', str(totalOtSampleLength/12))
    print(currentBatchDict)
    print(totalOtFullLength)

def resetCurrentBatchDict(): # sets currentBatchDict to default/empty values.
    currentBatchDict = {
        'batchDetails': {
            'ID':'',
            'material':'',
            'priority':0,
            'length':0
        },
        'OT':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Late':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Today':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Future':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
    }

    return


buildABatch()