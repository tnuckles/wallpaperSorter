#!usr/bin/env python

import getPdfData as getPdf
from math import floor

def calculateSample(globOfPdfs):
    count = len(globOfPdfs)
    return ((floor(count / 2) + (count % 2)) * 9.5)

def calculateFull(globOfPdfs): # Takes a list of paths to pdfs, calls sortPdfsByLength to srot them by length, then calculates their full length.
    sortedList = globOfPdfs
    totalPdfsLength = 0
    findOdd = False
    oddMatchHeight = 0
    for printPdf in sortedList:
        pdfLength = getPdf.length(printPdf)
        pdfOddOrEven = getPdf.oddOrEven(printPdf)
        pdfHeight = getPdf.height(printPdf)
        if (findOdd == False):
            totalPdfsLength += pdfLength
            if pdfOddOrEven == 1:
                findOdd = True
                oddMatchHeight = pdfHeight
        elif (findOdd == True):
            if pdfOddOrEven == 1:
                if oddMatchHeight == pdfHeight:
                    totalPdfsLength += (pdfLength - (pdfHeight + .5))
                    findOdd = False
                else:
                    totalPdfsLength += pdfLength
                    oddMatchHeight = pdfHeight
    return totalPdfsLength
    
def sortPdfs(pdfList):
    sortedByOdd = sortPdfsByOdd(pdfList)
    sortedByHeight = sortPdfsByHeight(sortedByOdd)
    sortedByLength = sortPdfsByLength(sortedByHeight)
    pdfList = combineMultiplePdfLists(sortedByLength)
    return pdfList

def sortPdfsByOdd(pdfList): # Takes a list of pathstopdfs and returns a dict of lists sorted by odd and even quantities, respectively.
    sortedPdfs = {
        'evenPdfs':[],
        'oddPdfs':[],
    }
    for printPdf in pdfList:
        pdfOdd = getPdf.oddOrEven(printPdf)
        if pdfOdd == 1:
            sortedPdfs['oddPdfs'].append(printPdf)
        else:
            sortedPdfs['evenPdfs'].append(printPdf)
    return sortedPdfs

def sortPdfsByHeight(pdfDict):# takes a dict of lists of pathstopdfs and sorts them by height, from greatest to least.
    sortedList = {
        '146.25':[],
        '136.25':[],
        '124.25':[],
        '112.25':[],
        '100.25':[],
        '88.25':[],
        '76.25':[],
        '64.25':[],
        '52.25':[],
        '40.25':[],
    }
    for listToSort in pdfDict:
        for printPdf in pdfDict[listToSort]:
            pdfHeight = str(getPdf.height(printPdf))
            sortedList[pdfHeight].append(printPdf)
        pdfDict[listToSort] = sortedList
        sortedList = {
            '146.25':[],
            '136.25':[],
            '124.25':[],
            '112.25':[],
            '100.25':[],
            '88.25':[],
            '76.25':[],
            '64.25':[],
            '52.25':[],
            '40.25':[],
        }
    return pdfDict

def sortPdfsByLength(pdfDict): # takes a list of pathstopdfs and sorts them by length, from greatest to least.
    listToSort = []
    sortedList = []
    for oddList in pdfDict:
        for heightList in pdfDict[oddList]:
            for printPdf in pdfDict[oddList][heightList]:
                pdfLength = getPdf.length(printPdf)
                listToSort.append((pdfLength, printPdf))
            listToSort.sort(reverse=True, key=lambda pdf: pdf[0])
            pdfList = listToSort
            listToSort = []
            for printPdf in pdfList:
                sortedList.append(printPdf[1])
            pdfDict[oddList][heightList] = sortedList
            sortedList = []
    return pdfDict

def sortPdfsByOrderNumber(pdfList): # takes a list of pathstopdfs and sorts them by orderNumber, from least to greatest.
    # Original sort code is at the bottom.
    listToSort = []
    sortedList = []
    for printPdf in pdfList:
        pdfOrderNumber = getPdf.orderNumber(printPdf)
        listToSort.append((pdfOrderNumber, printPdf))
    listToSort.sort(reverse=False, key=lambda pdf: pdf[0])
    pdfList = listToSort
    listToSort = []
    for printPdf in pdfList:
        sortedList.append(printPdf[1])
    pdfList = sortedList
    sortedList = []
    return pdfList
        
def combineMultiplePdfLists(pdfDict):
    sortedList = []
    for oddList in pdfDict:
        for heightList in pdfDict[oddList]:
            for printPdf in pdfDict[oddList][heightList]:
                sortedList.append(printPdf)
    return sortedList