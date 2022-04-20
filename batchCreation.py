#!usr/bin/env python

import os, shutil, math, datetime, time, json, glob, pikepdf
import zipfile as zf
from pathlib import Path
from datetime import date, timedelta, datetime
from sqlitedict import SqliteDict
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger, utils
from io import StringIO
import subprocess

import wallpaperSorterVariables as gv
from wallpaperSorter import main

def BatchOrdersMain():
    options = 1,2,3,4,5,6,0
    print('\n| Main Menu > Batch Orders')
    print('| 1. Batch Smooth Full')
    print('| 2. Batch Smooth Samples')
    print('| 3. Batch Woven Full')
    print('| 4. Batch Woven Samples')
    print('| 5. Batch the whole damn thing')
    print('| 0. Return to Main Menu.')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return BatchOrdersMain()
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return BatchOrdersMain()
    if command == 1:
        confirm = confirmBatch('Smooth', 'Full')
        if confirm == True:
            batchingController('Smooth', 'Full')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 2:
        confirm = confirmBatch('Smooth', 'Sample')
        if confirm == True:
            batchingController('Smooth', 'Sample')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 3:
        confirm = confirmBatch('Woven', 'Full')
        if confirm == True:
            batchingController('Woven', 'Full')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 4:
        confirm = confirmBatch('Woven', 'Sample')
        if confirm == True:
            batchingController('Woven', 'Sample')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 5:
        batchingController('Woven', 'Full')
        batchingController('Woven', 'Sample')
        batchingController('Smooth', 'Full')
        batchingController('Smooth', 'Sample')
    elif command == 0:
        print('| Returning to Main Menu.')
        return main()

def confirmBatch(material, orderSize):
    options = 1,2
    print('\n| Confirm: Batch', material, orderSize, 'PDFs?')
    print('| 1. Yes')
    print('| 2. No')
    try:
        command = int(input('| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return confirmBatch(material, orderSize)
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return confirmBatch(material, orderSize)
    if command == 1:
        return True
    elif command == 2:
        return False

def batchingController(material, orderSize):
    print('\n| Starting', material, orderSize, 'Batching.')
    materialLength = gv.dirLookupDict['MaterialLength'][material]
    # materialLength = int(input('\n| Please input your starting material length in feet > '))
    # while materialLength != type(int):
    #     materialLength = int(input('\n| Please input your starting material length in feet > '))
    BatchDir = BatchDirBuilder(material, orderSize)
    findOrdersForPrintv3(BatchDir, material, orderSize, (int(materialLength)))
    removeEmptyBatchFolders(True)
    # if orderSize == 'Full':
    #     findOrdersForPrintv3(BatchDir, material, orderSize, (int(materialLength)))
    #     removeEmptyBatchFolders(True)
    # else:
    #     findSampleOrdersForPrint(BatchDir, material, orderSize, (int(materialLength * 12)))
    print('\n| Finished Batching', material, orderSize, 'orders.')