#!usr/bin/env python

import shutil
from time import sleep
from datetime import date
import getPdfData as getPdf
from math import ceil, floor
from os import remove, walk, rename
from glob import glob
import wallpaperSorterVariables as gv
from batchCreate import tryToMovePDF

today = date.today()

def transferFilesFromDrive():
    # Old name convention: 300014719(1)-Watercolor Herringbone-Wv-Samp-Rp 4-Qty 1-W9-H25
    # New name convention: 300013884-1-(2022-02-02)-Stnd-Wv-Samp-Rp 2-Qty 1-Watercolor Herringbone-L9.5-W25-H9

    pdfDict = gv.dirLookupDict

    list_to_transfer = glob(gv.driveLocation + '/*.pdf')

    if len(list_to_transfer) < 1:
        print('\n| No files to transfer from Google Drive.')
        return
    
    for print_pdf in list_to_transfer:
        pdf_name = getPdf.name(print_pdf)
        pdf_friendly_name = getPdf.friendlyName(pdf_name)
        pdf_material = pdfDict[getPdf.material(pdf_name)]
        pdf_order_size = pdfDict[getPdf.size(pdf_name)]
        pdf_repeat = pdfDict[getPdf.repeat(pdf_name)]
        even_or_odd = pdfDict[getPdf.oddOrEven(pdf_name)]
        if pdf_order_size == 'Full':
            dest_path = gv.sortingDir + '3 - Today/' + pdf_material + pdf_order_size + pdf_repeat + even_or_odd + pdf_name
        else:
            dest_path = gv.sortingDir + '3 - Today/' + pdf_material + pdf_order_size + pdf_name
        print(f'\n| Trying to move {pdf_friendly_name}.')
        tryToMovePDF(print_pdf, dest_path, pdf_friendly_name, verbose=False)
    print('\n| Finished transferring files from Google Drive.')


    # for roots, dirs, files in walk(gv.driveLocation):
    #     ('\n| Renaming files in Google Drive to the new naming convention.')
    #     for file in files:
    #         if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
    #             continue
    #         elif file.endswith('.pdf') != True:
    #             continue
    #         else:
    #             try:
    #                 pdfDict = {
    #                     'orderNumber': file.split('(')[0],
    #                     'orderItem': file.split('(')[1].split(')')[0],
    #                     'templateName': file.split('-')[1],
    #                     'material': file.split('-')[2],
    #                     'orderSize': file.split('-')[3],
    #                     'orderRepeat': file.split('-')[4],
    #                     'orderQuantity': file.split('-')[5].split('Qty ')[1],
    #                     'orderWidth': file.split('-')[6],
    #                     'orderHeight': file.split('-')[7].split('.pdf')[0],
    #                 }
    #                 pdfDict['orderLength'] = str((ceil(int(pdfDict['quantity'])/2)*float(pdfDict['height']) + ((floor(int(pdfDict['quantity'])/2) * .5) + ((int(pdfDict['quantity']) % 2) * .5))))

    #                 if pdfDict['orderSize'] == 'Samp':
    #                     pdfDict['orderWidth'] = 'W25'
    #                     pdfDict['orderHeight'] = 'H9'
    #             except IndexError:
    #                 try:
    #                     pdfDict = getPdf.getAll(file)
    #                 except:
    #                     print('| Couldn\'t handle', file.split('/')[-1])
    #                     print('| Sorry about that.')
    #                     continue
    #         newPDFName = pdfDict['orderNumber'] + '-' + pdfDict['orderItem'] + '-(' + str(date.today()) + ')-Prty-' + pdfDict['material'] + '-' + pdfDict['orderSize'] + '-Rp ' + str(pdfDict['orderRepeat']) + '-Qty ' + str(pdfDict['orderQuantity']) + '-' + pdfDict['templateName'] + '-L' + str(pdfDict['orderLength']) + '-W' + str(pdfDict['orderWidth']) + '-H' + str(pdfDict['orderHeight']) + '.pdf'
    #         try:
    #             rename(gv.driveLocation + '/' + file, gv.driveLocation + '/' + newPDFName)
    #         except:
    #             print('\n| Trouble renaming files.\n| File:', file)
    #             print('\n| Returning to Main Menu. Sorry about this.')
    #             return    
    # print('| Pausing to allow name changing to update.')
    # sleep(4)
    # print('| Resuming')
    # print('| Moving files from Google Drive to today\'s sorted files.')
    # for roots, dirs, files in walk(gv.driveLocation):
    #     for file in files:
    #         if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
    #             continue
    #         elif file.endswith('.pdf') != True:
    #             continue
    #         else:
    #             pdfDict['orderRepeat'] = file.split('-')[8]
    #             pdfDict['orderQuantity'] = int(file.split('-')[9].split('Qty ')[1])
    #             if pdfDict['orderRepeat'] == 'Rp 2':
    #                 pdfDict['orderRepeat'] = 'Repeat 2/'
    #             else:
    #                 pdfDict['orderRepeat'] = 'Repeat Non-2/'
    #             if pdfDict['orderQuantity'] % 2 == 0:
    #                 pdfDict['orderQuantity'] = 'Even Panels/'
    #             else:
    #                 pdfDict['orderQuantity'] = 'Odd Panels/'
    #             print('| Moving file: ', file)
    #             print('| Source: ', gv.driveLocation)
    #             if pdfDict['orderSize'] == 'Full':
    #                 try:
    #                     shutil.move(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']]+ pdfDict['orderRepeat'] + pdfDict['orderQuantity'])
    #                     sleep(2)
    #                     print('| Successfully transferred! File:', file)
    #                 except shutil.Error:
    #                     shutil.copy(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']]+ pdfDict['orderRepeat'] + pdfDict['orderQuantity'])
    #                     try:
    #                         remove(gv.driveLocation + '/' + file)
    #                         sleep(2)
    #                         print('| Successfully transferred! File:', file)
    #                     except OSError:
    #                         print('|> Could not move ' + file)
    #                 except OSError as err:
    #                     print(err)    
    #             elif pdfDict['orderSize'] == 'Samp':
    #                 try:
    #                     shutil.move(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']])
    #                     sleep(2)
    #                     print('| Successfully transferred! File:', file)
    #                 except shutil.Error:
    #                     shutil.copy(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']])
    #                     try:
    #                         remove(gv.driveLocation + '/' + file)
    #                         sleep(2)
    #                         print('| Successfully transferred! File:', file)
    #                     except OSError:
    #                         print('|> Could not move ' + file)
    #                 except PermissionError:
    #                     shutil.copy(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']])
    #                     try:
    #                         remove(gv.driveLocation + '/' + file)
    #                         sleep(2)
    #                         print('| Successfully transferred! File:', file)
    #                     except OSError:
    #                         print('|> Could not move ' + file)
    # print('\n| Finished transferring files from Google Drive.')
    # #moveForDueDates()
    return