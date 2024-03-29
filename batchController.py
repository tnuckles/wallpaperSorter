#!usr/bin/env python

import batchMenu as bMenu
from batchCreate import getPdfGlob
from batchSorting import calculateFull, calculateSample, sortPdfs, sortPdfsByOrderNumber
from batchCreate import createBatch, createBatchFolderAndMovePdfs
from wallpaperSorterVariables import getUtilityFiles

### Global Variables

minLength = 0.8 # minimum length as a percent

currentBatchDict = {
        'batchDetails': {
            'ID':'',
            'material':'',
            'priority':0,
            'length':2,
            'materialLength':0,
            'careAboutminLength':True,
            'includeOTs':False,
            'colorGuides':{
                'default':getUtilityFiles['colorGuide'],
                'uniqueFilename':''
            },
            'rollStickers':{
                'default':getUtilityFiles['rollSticker'],
                'uniqueFilename':''
            },
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
        'Tomorrow':{
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
        'Tomorrow':{
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
    if batchDetails == False:
        return
    currentBatchDict['batchDetails']['includeOTs'] = otCheck(batchDetails['material'])
    bMenu.confirmBatchMenu(batchDetails['material'],int(batchDetails['materialLength']/12))
    
    # adds the details from the previous section
    currentBatchDict['batchDetails']['ID'] = bMenu.getBatchID()
    currentBatchDict['batchDetails']['material'] = batchDetails['material']
    currentBatchDict['batchDetails']['materialLength'] = batchDetails['materialLength']
    currentBatchDict['batchDetails']['careAboutminLength'] = batchDetails['minLength']
    
    #variables of the currentBatchDict for easy reference
    material = currentBatchDict['batchDetails']['material']
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
    tomorrowLength = availablePdfs['Tomorrow']['full']['batchLength'] + availablePdfs['Tomorrow']['sample']['batchLength']
    futureLength = availablePdfs['Future']['full']['batchLength'] + availablePdfs['Future']['sample']['batchLength']
    potentialBatchLength = otLength + lateLength + todayLength + tomorrowLength + futureLength
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
    '''Tomorrow Pdfs'''
    availablePdfs['Tomorrow']['full']['batchList'] = sortPdfs(getPdfGlob('Tomorrow', material, 'full'))
    availablePdfs['Tomorrow']['full']['batchLength'] = calculateFull(availablePdfs['Tomorrow']['full']['batchList'])
    availablePdfs['Tomorrow']['sample']['batchList'] = sortPdfsByOrderNumber(getPdfGlob('Tomorrow', material, 'sample'))
    availablePdfs['Tomorrow']['sample']['batchLength'] = calculateSample(availablePdfs['Tomorrow']['sample']['batchList'])
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
            'length':2,
            'materialLength':0,
            'careAboutminLength':True,
            'includeOTs':False,
            'colorGuides':{
                'default':getUtilityFiles['colorGuide'],
                'uniqueFilename':''
            },
            'rollStickers':{
                'default':getUtilityFiles['rollSticker'],
                'uniqueFilename':''
            },
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
        'Tomorrow':{
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
        'Tomorrow':{
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