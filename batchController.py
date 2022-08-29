#!usr/bin/env python

import batchMenu as bMenu
from batchCreate import getPdfGlob
from batchSorting import calculateFull, calculateSample, sortPdfs, sortPdfsByOrderNumber
from batchCreate import createBatch, createBatchFolderAndMovePdfs
from wallpaperSorterVariables import getHeader

### Global Variables

minLength = 0.8 # minimum length as a percent

currentBatchDict = {
        'batchDetails': {
            'ID':'',
            'material':'',
            'priority':0,
            'length':0,
            'materialLength':0,
            'careAboutminLength':True,
            'includeOTs':False,
            'colorGuides':{
                'default':'/opt/caldera/var/public/z_Storage/Utility/LvD Color Chart Rotated.pdf',
                'uniqueFilename':''
            },
            'rollStickers':{
                'default':'/opt/caldera/var/public/z_Storage/Utility/LvD Color Chart Rotated.pdf',
                'uniqueFilename':''
            },
        },
        'OT':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['ot']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['ot']
            },
            'header':'',
        },
        'Late':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['late']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['late']
            },
            'header':'',
        },
        'Today':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['today']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['today']
            },
            'header':'',
        },
        'Future':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['future']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['future']
            },
            'header':'',
        },
    }

availablePdfs = {
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
    currentBatchDict = resetCurrentBatchDict()

    # Prompts user for batch information and confirms their selection
    batchDetails = bMenu.batchDetailsMenu()
    currentBatchDict['batchDetails']['includeOTs'] = otCheck(batchDetails['material'])
    bMenu.confirmBatchMenu(batchDetails['material'],int(batchDetails['materialLength']/12))
    
    # adds the details from the previous section
    currentBatchDict['batchDetails']['ID'] = bMenu.getBatchID()
    currentBatchDict['batchDetails']['material'] = batchDetails['material']
    currentBatchDict['batchDetails']['materialLength'] = batchDetails['materialLength']
    currentBatchDict['batchDetails']['careAboutminLength'] = batchDetails['minLength']
    
    #variables of the currentBatchDict for easy reference
    material = currentBatchDict['batchDetails']['material']
    includeOTs = currentBatchDict['batchDetails']['includeOTs']
    materialLength = batchDetails['materialLength']
    minBatchLength = batchDetails['materialLength'] * minLength

    # gets available print PDFs
    fillAvailablePdfsDict(material)
    
    # if we're caring about min length, check here to ensure there's enough to meet the min length
    if batchDetails['minLength'] == True:
        checkminLength(material, minBatchLength)
    
    # Begin batch creation
    createBatch(currentBatchDict, availablePdfs)
    createBatchFolderAndMovePdfs(currentBatchDict)

    # Resets dicts and returns to batching menu
    return resetDicts()
    

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

def otCheck(material):
    otFullCount = len(getPdfGlob('OT', material, 'full'))
    otSampCount = len(getPdfGlob('OT', material, 'Sample'))
    if (otFullCount > 0) or (otSampCount > 0):
        print('| Full', material, 'Order Troubles:', str(otFullCount))
        print('| Sample', material, 'Order Troubles:', str(otSampCount))
        return bMenu.includeOTs()
    else:
        return False

def checkminLength(material, minBatchLength):
    otLength = availablePdfs['OT']['full']['batchLength'] + availablePdfs['OT']['sample']['batchLength']
    lateLength = availablePdfs['Late']['full']['batchLength'] + availablePdfs['Late']['sample']['batchLength']
    todayLength = availablePdfs['Today']['full']['batchLength'] + availablePdfs['Today']['sample']['batchLength']
    futureLength = availablePdfs['Future']['full']['batchLength'] + availablePdfs['Future']['sample']['batchLength']
    potentialBatchLength = otLength + lateLength + todayLength + futureLength
    #potentialBatchLength = sortPdfs(getPdfGlob('all', material, 'all'))
    if potentialBatchLength < minBatchLength:
        print('| Not enough', material, 'PDFs to fill up 80' + "% " + 'of a roll.')
        return buildABatch()
    else:
        return

def fillAvailablePdfsDict(material):
    '''OT Pdfs'''
    # gets a sorted list of OT Full Pdfs
    availablePdfs['OT']['full']['batchList'] = sortPdfs(getPdfGlob('OT', material, 'full'))
    # gets a length for the sorted list of OT Full Pdfs
    availablePdfs['OT']['full']['batchLength'] = calculateFull(availablePdfs['OT']['full']['batchList'])
    # gets a list of OT Sample Pdfs
    availablePdfs['OT']['sample']['batchList'] = sortPdfsByOrderNumber(getPdfGlob('OT', material, 'sample'))
    # gets a length of OT Sample Pdfs
    availablePdfs['OT']['sample']['batchLength'] = calculateSample(availablePdfs['OT']['sample']['batchList'])
    '''Late Pdfs'''
    availablePdfs['Late']['full']['batchList'] = sortPdfs(getPdfGlob('Late', material, 'full'))
    availablePdfs['Late']['full']['batchLength'] = calculateFull(availablePdfs['Late']['full']['batchList'])
    availablePdfs['Late']['sample']['batchList'] = sortPdfsByOrderNumber(getPdfGlob('Late', material, 'sample'))
    availablePdfs['Late']['sample']['batchLength'] = calculateSample(availablePdfs['Late']['sample']['batchList'])
    '''Today Pdfs'''
    availablePdfs['Today']['full']['batchList'] = sortPdfs(getPdfGlob('Today', material, 'full'))
    availablePdfs['Today']['full']['batchLength'] = calculateFull(availablePdfs['Today']['full']['batchList'])
    availablePdfs['Today']['sample']['batchList'] = sortPdfsByOrderNumber(getPdfGlob('Today', material, 'sample'))
    availablePdfs['Today']['sample']['batchLength'] = calculateSample(availablePdfs['Today']['sample']['batchList'])
    '''Future Pdfs'''
    availablePdfs['Future']['full']['batchList'] = sortPdfs(getPdfGlob('Future', material, 'full'))
    availablePdfs['Future']['full']['batchLength'] = calculateFull(availablePdfs['Future']['full']['batchList'])
    availablePdfs['Future']['sample']['batchList'] = sortPdfsByOrderNumber(getPdfGlob('Future', material, 'sample'))
    availablePdfs['Future']['sample']['batchLength'] = calculateSample(availablePdfs['Future']['sample']['batchList'])

def resetDicts():
    availablePdfs = resetAvailablePdfs()
    currentBatchDict = resetCurrentBatchDict()
    return buildABatch()

def resetCurrentBatchDict(): # sets currentBatchDict to default/empty values.
    currentBatchDict = {
        'batchDetails': {
            'ID':'',
            'material':'',
            'priority':0,
            'length':0,
            'materialLength':0,
            'careAboutminLength':True,
            'includeOTs':False,
            'colorGuides':{
                'default':'/opt/caldera/var/public/z_Storage/Utility/LvD Color Chart Rotated.pdf',
                'uniqueFilename':''
            },
            'rollStickers':{
                'default':'/opt/caldera/var/public/z_Storage/Utility/LvD Color Chart Rotated.pdf',
                'uniqueFilename':''
            },
        },
        'OT':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['ot']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['ot']
            },
            'header':'',
        },
        'Late':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['late']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['late']
            },
            'header':'',
        },
        'Today':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['today']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['today']
            },
            'header':'',
        },
        'Future':{
            'full':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['future']
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
                'header':getHeader['future']
            },
            'header':'',
        },
    }

    return currentBatchDict

def resetAvailablePdfs():
    availablePdfs = {
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

    return availablePdfs

#buildABatch()