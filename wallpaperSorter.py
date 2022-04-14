#!usr/bin/env python

import os, shutil, math, datetime, time, json, glob, pikepdf
import zipfile as zf
from pathlib import Path
from datetime import date, timedelta, datetime
from sqlitedict import SqliteDict
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger, utils
from io import StringIO
import subprocess

#Location for Caldera's Folders
if os.path.expanduser('~').split('/')[-1] == 'Trevor':
    calderaDir = '/opt/caldera/var/public/'
    driveLocation = '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment'
else:
    calderaDir = '/Volumes/Print Drive/caldera/public/'
    driveLocation = '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Fulfillment'

orderdb = calderaDir + 'z_Storage/z_WallpaperDB/lvdOrderDatabase.sqlite'
ordersDict = SqliteDict(orderdb, autocommit=True)
QueueCounterDB = calderaDir + 'z_Storage/z_WallpaperDB/lvdGlobalQueueCounter.sqlite'
globalQueueCounter = SqliteDict(QueueCounterDB, autocommit=True)
#globalQueueCounter['QueueCounter'] = 1

QueueFoldersDir = calderaDir + '2 Queue Folders/'
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
        'Smooth':145 * 12,
        'Woven':98 * 12,
        'Traditional':98 * 12,
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

countOfRefPDFs = { #Running count of PDFs that are referenced during sample creating. If a PDF is referenced more than once, the order and PDF are printed to alert fulfillment of dual-type samples
    
}

orderItemsDict = {
}

today = date.today()

### Definitions
### Definitions

def main():
    options = 1,2,3,4,5,6,0
    print('\n| Main Menu')
    print('| 1. Sort Orders')
    print('| 2. Download Orders from Google Drive')
    print('| 3. Queue Orders')
    print('| 4. Update Sorting Based on Due Dates')
    print('| 6. Test Queues')
    print('| 5. Quit')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return main()
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return main()
    if command == 1:
        findJSONs()
        reportDuplicatePDFs()
        splitMultiPagePDFs()
        if os.path.expanduser('~').split('/')[-1] == 'Trevor':
            checkRepeatSize()
        sortPDFsByDetails()
        buildDBSadNoises()
        return main()
    elif command == 2:
        transferFilesFromDrive()
        return main()
    elif command == 3:
        QueueOrdersMain()
        return main()
    elif command == 4:
        moveForDueDates()
        return main()
    elif command == 6:
        buildAQueue('Queue 1', 'Smooth', 150, 'Full')
        return main()
    elif command == 5:
        print('\n| Goodbye!')
        pass
    elif command == 0:
        if os.path.expanduser('~').split('/')[-1] == 'Trevor':
            print('\n| The creator is among us.')
            print('| Prepping folders for test.')
            fullOrPartialRun = input('| Do you want to do a full run? > ')
            if fullOrPartialRun == 'y':
                shutil.rmtree(QueueFoldersDir)
                os.mkdir(QueueFoldersDir)
                shutil.rmtree(downloadDir)
                shutil.copytree('/Users/Trevor/Desktop/Backup/Downloaded', downloadDir)
                # shutil.rmtree(sortingDir)
                # shutil.copytree('/Users/Trevor/Desktop/Backup/5 Sorted for Print', sortingDir)
                findJSONs()   
                reportDuplicatePDFs()
                #splitMultiPagePDFs()
                checkRepeatSize()
                sortPDFsByDetails()
            transferFromDrive = input('| Do you want to transfer files from drive?\n| This will copy the current directory to a test directory. > ')
            if transferFromDrive == 'y':
                shutil.rmtree('/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment')
                shutil.copytree('/Volumes/GoogleDrive/Shared drives/# Production/#LvD Fulfillment', '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment')
                transferFilesFromDrive()
            buildAQueue('Queue 1', 'Smooth', 150, 'Full')
            return main()
    print('\n| Job\'s Done!')

def startupChecks():
    checkOrderDirectoryStructure()
    checkQueueCounter()
    moveForDueDates()

def checkQueueCounter():
    if globalQueueCounter['QueueCounter'] > 9000:
        globalQueueCounter['QueueCounter'] = 1

def buildSortedDirStructure(parentFolder):
    os.mkdir(parentFolder + 'Smooth/')
    os.mkdir(parentFolder + 'Smooth/Sample')
    os.mkdir(parentFolder + 'Smooth/Full/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat 2/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat 2/Even Panels/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat 2/Odd Panels/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat Non-2/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat Non-2/Even Panels/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat Non-2/Odd Panels/')
    os.mkdir(parentFolder + 'Woven/')
    os.mkdir(parentFolder + 'Woven/Sample')
    os.mkdir(parentFolder + 'Woven/Full/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat 2/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat 2/Even Panels/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat 2/Odd Panels/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat Non-2/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat Non-2/Even Panels/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat Non-2/Odd Panels/')
    return

def checkOrderDirectoryStructure():
    if Path(calderaDir + '# Past Orders/Original Files/').exists() == False:
        try:
            os.mkdir(calderaDir + '# Past Orders/Original Files')
        except:
            pass
    if Path(sortingDir + '1 - Late and OT/').exists() == True:
        try:
            os.mkdir(sortingDir + '1 - OT Orders/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '1 - OT Orders/')
        try:
            os.mkdir(sortingDir + '2 - Late/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '2 - Late/')
    if Path(sortingDir + '2 - Today/').exists() == True:
        try:
            os.mkdir(sortingDir + '3 - Today/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '3 - Today/')
    if Path(sortingDir + '3 - Future/').exists() == True:
        try:
            os.mkdir(sortingDir + '4 - Future/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '4 - Future/')
    return

def moveForDueDates():
    print('\n| Updating Orders. Today\'s date:', today)
    for file in glob.iglob(sortingDir + '**/*.pdf', recursive=True):
        fileName = file.split('/')[-1]
        orderDueDate = datetime.date(datetime.strptime(fileName.split('(')[1].split(')')[0], '%Y-%m-%d')) 
        material = fileName.split('-')[6]
        orderSize = fileName.split('-')[7]
        repeat = int(fileName.split('-')[8].split(' ')[1])
        oddOrEven = int(fileName.split('-')[9].split(' ')[1]) % 2   
        orderLength = float(fileName.split('-')[11].split('L')[1])
        if orderDueDate < today:
            orderDueDate = '2 - Late/'
        elif orderDueDate > today:
            orderDueDate = '4 - Future/'
        else:
            orderDueDate = '3 - Today/'
         # Checks if order is over the maximum length of a roll and moves it to Needs Attention
        if material == 'Wv':
            if orderLength >= dirLookupDict['MaterialLength']['Woven']:
                try:
                    shutil.copy(file, needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        elif material == 'Sm':
            if orderLength >= dirLookupDict['MaterialLength']['Smooth']:
                try:
                    shutil.copy(file, needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        if orderSize == 'Samp':
            try:
                shutil.move(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Sample/')
                print('| Updated:', file.split('/')[-1])
            except:
                try:
                    shutil.copy(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Sample/')
                    os.remove(file)
                    print('| Updated:', file.split('/')[-1])
                except shutil.SameFileError:
                    continue
        else:
            try:
                shutil.move(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Full/' + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                print('| Updated:', file.split('/')[-1])
            except:
                try:
                    shutil.copy(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Full/' + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    os.remove(file)
                    print('| Updated:', file.split('/')[-1])
                except shutil.SameFileError:
                    continue
    print('| Done updating orders based on Due Dates.')
    
    needsAttentionDir = len(glob.glob(needsAttention + '*.pdf'))
    if needsAttentionDir > 0:
        print(f'\n| ****\n| 4 Needs Attention has {needsAttentionDir} file(s) that need attention.\n| ****\n')  

def findJSONs(): #iterates over a given folder, unzips files, finds JSON files, and calls parseJSONDerulo
    os.chdir(downloadDir)
    for roots, dirs, files in os.walk(downloadDir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext == '.zip':
                try:
                    with zf.ZipFile(file, 'r') as zip_ref:
                        zip_ref.extractall(downloadDir)
                    os.remove(file)
                except:
                    print('Couldn\'t unzip file:', file)
    for roots, dirs, files in os.walk(downloadDir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if file.startswith('.'): #skips macOS X Hidden file '.DS_Store'
                continue
            elif ext == '.xml':
                try:
                    os.remove(file)
                except OSError:
                    print('| Could not remove ' + file)
            else:
                if ext == '.json':
                    with open(file) as file:
                        JSONDerulo = json.load(file)
                    parseJSONDerulo(JSONDerulo)
    for roots, dirs, files in os.walk(downloadDir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext == '.json':
                try:
                    os.remove(file)
                except OSError:
                    print('| Could not remove ' + file)
            else:
                try:
                    if (file.split('_')[-2] == 'bi') or (file.split('_')[-3] == 'lvd'):
                        os.remove(file)
                except IndexError:
                    continue

def parseJSONDerulo(JSON): #reads through an JSON file, finds the appropriate information for related PDFs, and renames files
    count = 1
    JSONitem = JSON['order']['item']
    orderNumber = JSON['orderNumber']
    keepTrackOfOrderNumber(orderNumber)
    orderDueDate = JSON['orderDueDate']
    shipVia = shippingMethods[JSON['shippingInfo']['method']['shipvia']]
    try:
        for itemNum in range(len(JSONitem)):
            originalPDFName = JSONitem[itemNum]['filename']
            itemID = originalPDFName.split('_')[0]
            try:
                templateName = JSONitem[itemNum]['description'].split(' ')[2] + ' ' + JSONitem[itemNum]['description'].split(' ')[3]
            except IndexError:
                templateName = JSONitem[itemNum]['description'].split(' Wallpaper')[0]
            paperType = substrate[JSONitem[itemNum]['paper']]
            quantity = JSONitem[itemNum]['quantityOrdered']
            height = JSONitem[itemNum]['height'] 
            width = JSONitem[itemNum]['width']
            repeat = JSONitem[itemNum]['wallpaperRepeat']
            orderTroubleNotes = JSON['order_trouble_notes']
            if width == '9':
                orderSize = 'Samp'
                length = '9.5'
                height = '9'
                width = '25'
            else:
                width = str(int(width) * int(quantity) + 1)
                height = str(int(height) + 4.25)
                if height == '148.25':
                    height = '146.25'
                orderSize = 'Full'
                length = str((math.ceil(int(quantity)/2)*float(height) + ((math.floor(int(quantity)/2) * .5) + ((int(quantity) % 2) * .5))))
                # See Length Notes at the end of the function for an explanation.
            newPDFName = orderNumber + '-' + str(count) + '-(' + orderDueDate + ')-' + shipVia + '-' + paperType + '-' + orderSize + '-Rp ' + repeat.split("'")[0] + '-Qty ' + quantity + '-' + templateName + '-L' + length + '-W' + width + '-H' + height
            renamePDF(originalPDFName, newPDFName)
            keepTrackOfPDF(orderNumber, originalPDFName) 
            count += 1
            if orderNumber in orderItemsDict:
                orderItemsDict[orderNumber][itemID] = {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': paperType,
                    'Order Size': orderSize,
                    'Repeat': repeat.split('\'')[0],
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': length,
                    'Width': width,
                    'Height': height,
                    'OT Notes': orderTroubleNotes,
                    'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                }
            else:
                orderItemsDict[orderNumber] = {
                    itemID : {
                        'Status': 'Sorted',
                        'Due Date': orderDueDate,
                        'Shipping': shipVia,
                        'Material': paperType,
                        'Order Size': orderSize,
                        'Repeat': repeat.split('\'')[0],
                        'Quantity': quantity,
                        'Template': templateName,
                        'Length': length,
                        'Width': width,
                        'Height': height,
                        'OT Notes': orderTroubleNotes,
                        'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                    }
                }
                    
    except KeyError:
        originalPDFName = JSONitem['filename']
        itemID = originalPDFName.split('_')[0]
        templateName = JSONitem['description'].split(' Wallpaper')[0]
        paperType = substrate[JSONitem['paper']]
        quantity = JSONitem['quantityOrdered']
        height = JSONitem['height']
        width = JSONitem['width']
        repeat = JSONitem['wallpaperRepeat']
        orderTroubleNotes = JSON['order_trouble_notes']
        if width == '9':
            orderSize = 'Samp'
            length = '9.5'
            height = '9'
            width = '25'
        else:
            width = str(int(width) * int(quantity) + 1)
            height = str(int(height) + 4.25)
            if height == '148.25':
                height = '146.25'
            orderSize = 'Full'
            length = str((math.ceil(int(quantity)/2)*float(height) + ((math.floor(int(quantity)/2) * .5) + ((int(quantity) % 2) * .5))))
        newPDFName = orderNumber + '-' + str(count) + '-(' + orderDueDate + ')-' + shipVia + '-' + paperType + '-' + orderSize + '-Rp ' + repeat.split("'")[0] + '-Qty ' + quantity + '-' + templateName + '-L' + length + '-W' + width + '-H' + height
        renamePDF(originalPDFName, newPDFName)
        keepTrackOfPDF(orderNumber, originalPDFName) 
        count += 1
        if orderNumber in orderItemsDict:
                orderItemsDict[orderNumber][itemID] = {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': paperType,
                    'Order Size': orderSize,
                    'Repeat': repeat.split('\'')[0],
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': length,
                    'Width': width,
                    'Height': height,
                    'OT Notes': orderTroubleNotes,
                    'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                }
        else:
            orderItemsDict[orderNumber] = {
                itemID : {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': paperType,
                    'Order Size': orderSize,
                    'Repeat': repeat.split('\'')[0],
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': length,
                    'Width': width,
                    'Height': height,
                    'OT Notes': orderTroubleNotes,
                    'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                }
            }
    
    ''' # Length Notes: I will never remember why I did this. Here are my notes. The length is the length of material an order will take up.
        # Length Notes: The above equation takes the quantity and divides it by two since we can fit two panels side by side.
        # Length Notes: it then multiplies that by the height to get the overall length of material.
        # Length Notes: after, it takes the quantity/2, rounds it down, and multiplies it by .5 for the .5" gap between each panel.
        # Length Notes: lastly, it takes the quantity % 2 to see if the quantity is odd or not. If the quantity is odd, then it will add on one more length of .5"
        # Length Notes: for the times that a panel is by itself and still has another .5" section.'''

def renamePDF(old, new):
    extension = old.split(".")[-1]
    itemName = new + "." + extension
    try:
        shutil.copy(old, old + ' - temp')
        os.rename(old, itemName)
        os.rename(old + ' - temp', old)
    except OSError:
        print("\n| Error Renaming. PDF may not exist in package." + "\n| Original File Name: " + old + "\n| New Item Name: " + itemName + "\n| *** Please check order", itemName.split("-")[0],"***")

def keepTrackOfOrderNumber(orderNumber): #keeps track of the original PDF names to alert fulfillment to multi-paper type PDFs
    if orderNumber in countOfRefPDFs:
        pass
    else:
        countOfRefPDFs[orderNumber] = {}

def keepTrackOfPDF(orderNumber, pdfFileName):
    if pdfFileName in countOfRefPDFs[orderNumber]:
        countOfRefPDFs[orderNumber][pdfFileName] += 1
    else:
        countOfRefPDFs[orderNumber][pdfFileName] = 1

def reportDuplicatePDFs(): #prints out any PDFs from keepTrackOfOrderNumber() that have a count of 2 or more
    for orderNumber in countOfRefPDFs:
        for pdfName in countOfRefPDFs[orderNumber]:
            if countOfRefPDFs[orderNumber][pdfName] > 1:
                print('\n| The following Order has samples with multiple material types:')
                print('| ' + orderNumber + ': ' + pdfName.replace('_',' '))

def splitMultiPagePDFs():
    for file in glob.iglob(downloadDir + '*.pdf'):
        try:
            pdf = pikepdf.Pdf.open(file)
            NumOfPages = len(pdf.pages)
        except:
            print(f'| Couldn\'t check the number of pages on {file}')
            pass
        if NumOfPages > 1:
                print(f'| {file} has more than one page in its PDF. Splitting now.')
                templateName = file.split('-')[10] ##
                namePt1 = file.split('Qty ')[0] + 'Qty '
                namePt2 = file.split(templateName)[1]
                repeat = file.split('-')[8] ##
                quantity = int(file.split('-')[9].split(' ')[1])
                for n, page in enumerate(pdf.pages):
                    dst = pikepdf.Pdf.new()
                    dst.pages.append(page)
                    dst.save(namePt1 + str(quantity) + '-' + templateName + ' Panel ' + str(n + 1) + namePt2)
                try:
                    os.remove(file)
                    print(f'| Finished splitting {file}')
                except:
                    print(f'| Split the pages of {file},\nbut couldn\'t remove the original.')

def sortPDFsByDetails():
    print('\n| Starting Sort Process. This may take a long time.')
    for file in glob.iglob(downloadDir + '*.pdf'):
        dueDate = datetime.date(datetime.strptime(file.split('(')[1].split(')')[0], '%Y-%m-%d'))
        material = file.split('-')[6]
        orderSize = file.split('-')[7]
        repeat = int(file.split('-')[8].split(' ')[1])
        oddOrEven = int(file.split('-')[9].split(' ')[1]) % 2
        orderLength = float(file.split('-')[11].split('L')[1])
        # Checks if order is over the maximum length of a roll and moves it to Needs Attention
        if material == 'Wv':
            if orderLength >= dirLookupDict['MaterialLength']['Woven']:
                try:
                    shutil.copy(file, needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                            print(err)
        elif material == 'Sm':
            if orderLength >= dirLookupDict['MaterialLength']['Smooth']:
                try:
                    shutil.copy(file, needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        # Sorts based on normal parameters.            
        if orderSize == 'Samp':
            if dueDate < date.today():
                try:
                    shutil.copy(file, sortingDir + '2 - Late/' + dirLookupDict[material] +dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            elif dueDate > date.today():
                try:
                    shutil.copy(file, sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            else:
                try:
                    shutil.copy(file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        else:
            if dueDate < date.today():
                try:
                    shutil.copy(file, sortingDir + '2 - Late/' + dirLookupDict[material] +dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            elif dueDate > date.today():
                try:
                    shutil.copy(file, sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            else:
                try:
                    shutil.copy(file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
    
    print('| Finished sorting files.')
    needsAttentionDir = len(glob.glob(needsAttention + '*.pdf'))
    if needsAttentionDir > 0:
        print(f'\n| ****\n| 4 Needs Attention has {needsAttentionDir} file(s) that need attention.\n| ****\n')

def buildDBSadNoises():
    print('| Building DB. Please hold.')
    fullOrdersDirectory = sortingDir + '**/Full/*.pdf' 
    #300014839-2-(2022-02-15)-Stnd-Sm-Samp-Rp 2-Qty 1-Mod Herons-L9.5-W25-H9
    # buildDBSadNoises()
    # print('| Printing Current Order Database.')
    # for order in orderItemsDict:
    #    print(f'|-{order}')
    #    for orderItemID in orderItemsDict[order]:
    #        if orderItemsDict[order][orderItemID]['Order Size'] == 'Full':
    #            print(f'|  -- {orderItemID}')
    #            print('|    --', orderItemsDict[order][orderItemID]['Status'])
    #            print('|    --', orderItemsDict[order][orderItemID]['Order Size'])
    #            print('|    --', orderItemsDict[order][orderItemID]['Length'])
    #            print('|    --', orderItemsDict[order][orderItemID]['Repeat'])
    for printPDF in glob.iglob(sortingDir + '**/*.pdf', recursive=True):
        orderItemID = 1
        fileName = printPDF.split('/')[-1].split('.pdf')[0]
        orderNumber = fileName.split('-')[0]
        orderDueDate = datetime.date(datetime.strptime(fileName.split('(')[1].split(')')[0], '%Y-%m-%d'))
        shipVia = fileName.split('-')[5]
        material = fileName.split('-')[6]
        orderSize = fileName.split('-')[7]
        repeat = int(fileName.split('-')[8].split(' ')[1])
        quantity = int(fileName.split('-')[9].split(' ')[1])
        oddOrEven = quantity % 2
        templateName = fileName.split('-')[10]
        orderLength = float(fileName.split('-')[11].split('L')[1])
        orderWidth = int(fileName.split('-')[12].split('W')[1])
        orderHeight = float(fileName.split('-')[13].split('H')[1])
        if orderNumber[orderItemID] in orderItemsDict:
            orderItemsDict[orderNumber][orderItemID] = {
                'Status': 'Sorted',
                'Due Date': orderDueDate,
                'Shipping': shipVia,
                'Material': material,
                'Order Size': orderSize,
                'Repeat': repeat,
                'Quantity': quantity,
                'Odd': oddOrEven,
                'Template': templateName,
                'Length': orderLength,
                'Width': orderWidth,
                'Height': orderHeight,
                'File Path': fileName
            }
        else:
            orderItemsDict[orderNumber] = {
                orderItemID : {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': material,
                    'Order Size': orderSize,
                    'Repeat': repeat,
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': orderLength,
                    'Width': orderWidth,
                    'Height': orderHeight,
                    'File Path': fileName
                }
            }
    print('| DB Built.')

def QueueOrdersMain():
    options = 1,2,3,4,5,0
    print('\n| Main Menu > Queue Orders')
    print('| 1. Queue Smooth Full')
    print('| 2. Queue Smooth Samples')
    print('| 3. Queue Woven Full')
    print('| 4. Queue Woven Samples')
    print('| 5. Combine Queues')
    print('| 0. Return to Main Menu.')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return QueueOrdersMain()
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return QueueOrdersMain()
    if command == 1:
        confirm = confirmQueue('Smooth', 'Full')
        if confirm == True:
            QueueingController('Smooth', 'Full')
            return QueueOrdersMain()
        elif confirm == False:
            print('\n| Returning to Queue Orders.')
            return QueueOrdersMain()
    elif command == 2:
        confirm = confirmQueue('Smooth', 'Sample')
        if confirm == True:
            QueueingController('Smooth', 'Sample')
            return QueueOrdersMain()
        elif confirm == False:
            print('\n| Returning to Queue Orders.')
            return QueueOrdersMain()
    elif command == 3:
        confirm = confirmQueue('Woven', 'Full')
        if confirm == True:
            QueueingController('Woven', 'Full')
            return QueueOrdersMain()
        elif confirm == False:
            print('\n| Returning to Queue Orders.')
            return QueueOrdersMain()
    elif command == 4:
        confirm = confirmQueue('Woven', 'Sample')
        if confirm == True:
            QueueingController('Woven', 'Sample')
            return QueueOrdersMain()
        elif confirm == False:
            print('\n| Returning to Queue Orders.')
            return QueueOrdersMain()
    elif command == 5:
        material = input('| Material please > ')
        combineQueueFoldersController(material)
    elif command == 0:
        print('| Returning to Main Menu.')
        return main()

def confirmQueue(material, orderSize):
    options = 1,2
    print('\n| Confirm: Queue', material, orderSize, 'PDFs?')
    print('| 1. Yes')
    print('| 2. No')
    try:
        command = int(input('| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return confirmQueue(material, orderSize)
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return confirmQueue(material, orderSize)
    if command == 1:
        return True
    elif command == 2:
        return False

def QueueingController(material, orderSize):
    print('\n| Starting', material, orderSize, 'Full Queueing.')
    materialLength = int(input('\n| Please input your starting material length in feet > '))
    # while materialLength != type(int):
    #     materialLength = int(input('\n| Please input your starting material length in feet > '))
    QueueDir = QueueDirBuilder(material, orderSize)
    if orderSize == 'Full':
        findOrdersForPrint2Ptv2(QueueDir, material, orderSize, (int(materialLength)*12))
        removeEmptyQueueFolders(True)
        #combineQueueFoldersController(material)
        QueueDir = QueueDirBuilder(material, orderSize)
        findOrdersForPrint4Ptv2(QueueDir, material, orderSize, (int(materialLength)*12))
        removeEmptyQueueFolders(True)
    else:
        findSampleOrdersForPrint(QueueDir, material, orderSize, (int(materialLength * 12)))
    print('\n| Finished Queueing', material, orderSize, 'orders.')

def removeOldOrders(folderToClean, days): #removes folders and contents older than X days
    olderThanDays = days
    for subFolder in folderToClean.values(): #gets subfolder path
        for parentFolder, folder, file in os.walk(subFolder[1] + '/'): #
            folderName = os.path.basename(parentFolder) #extracts just the folder name from the folder path
            oldestDate = date.today() - timedelta(days=olderThanDays) #makes a variable to compare the date against
            try:
                if datetime.date(datetime.strptime(folderName, '%Y-%m-%d')) < oldestDate: #compares the date of the folder name against the oldest date
                   print('| ' + folderName + ' is older than ' + str(olderThanDays) + ' days. Thanos snapped it.') #Lets the user know an old directory and its contents has been deleted
                   shutil.rmtree(parentFolder) #removes folder
                else:
                    continue
            except ValueError:
                continue

def findSampleOrdersForPrint(QueueDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    curQueueDirLength = 0
    oddCount = 1
    if (curQueueDirLength < (materialLength - 10)):
        for sample in glob.iglob(lateOrders + '*.pdf'):
            if (curQueueDirLength + float(sample.split('/')[9].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
                os.rename(QueueDir, QueueFoldersDir + newQueueName)
                print('\n| Queue with OT/Late Orders Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
                QueueDir = QueueDirBuilder(material, orderSize)
                materialLength = input('| Please input your material length. > ')
                return findSampleOrdersForPrint(QueueDir, material, orderSize, int(materialLength)*12)
                # return findSampleOrdersForPrint(QueueDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                try:
                    shutil.move(sample, QueueDir)
                    if oddCount == 0:
                        curQueueDirLength += float(sample.split('/')[9].split('-')[11].split('L')[1])
                        oddCount = 1
                    else:
                        oddCount = 0
                except shutil.Error:
                    shutil.copy(sample, QueueDir)
                    try:
                        os.remove(sample)
                    except OSError:
                        print('|> Could not remove ' + sample)
                except FileNotFoundError:
                    print('|> Couldn\'t find sample to move. \n|> File: ', sample)
    if (curQueueDirLength < (materialLength - 10)):
        for sample in glob.iglob(todayOrders + '*.pdf'):
            if (curQueueDirLength + float(sample.split('/')[9].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
                os.rename(QueueDir, QueueFoldersDir + newQueueName)
                print('\n| Queue Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
                QueueDir = QueueDirBuilder(material, orderSize)
                materialLength = input('| Please input your material length. > ')
                return findSampleOrdersForPrint(QueueDir, material, orderSize, int(materialLength)*12)
                # return findSampleOrdersForPrint(QueueDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                try:
                    shutil.move(sample, QueueDir)
                    if oddCount == 0:
                        curQueueDirLength += float(sample.split('/')[9].split('-')[11].split('L')[1])
                        oddCount = 1
                    else:
                        oddCount = 0
                except shutil.Error:
                    shutil.copy(sample, QueueDir)
                    try:
                        os.remove(sample)
                    except OSError:
                        print('|> Could not remove ' + sample)
                except FileNotFoundError:
                    print('|> Couldn\'t find sample to move. \n|> File: ', sample)
    if (curQueueDirLength < (materialLength - 10)):
        for sample in glob.iglob(futureOrders + '*.pdf'):
            if (curQueueDirLength + float(sample.split('/')[9].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
                os.rename(QueueDir, QueueFoldersDir + newQueueName)
                print('\n| Queue Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
                QueueDir = QueueDirBuilder(material, orderSize)
                materialLength = input('| Please input your material length. > ')
                return findSampleOrdersForPrint(QueueDir, material, orderSize, int(materialLength)*12)
                # return findSampleOrdersForPrint(QueueDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                try:
                    shutil.move(sample, QueueDir)
                    if oddCount == 0:
                        curQueueDirLength += float(sample.split('/')[9].split('-')[11].split('L')[1])
                        oddCount = 1
                    else:
                        oddCount = 0
                except shutil.Error:
                    shutil.copy(sample, QueueDir)
                    try:
                        os.remove(sample)
                    except OSError:
                        print('|> Could not remove ' + sample)
                except FileNotFoundError:
                    print('|> Couldn\'t find sample to move. \n|> File: ', sample)                
    newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
    print('\n| Queue Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
    os.rename(QueueDir, QueueFoldersDir + newQueueName)
    return

def findFullRp2EvenOrdersForPrint(QueueDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    curQueueDirLength = 0
    while len(glob.glob(sortingDir + '*/'+ dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/Even Panels/*.pdf'))>0:
        if (curQueueDirLength < (materialLength - 0.85)):
            for order in glob.iglob(lateOrders + 'Repeat 2/Even Panels/*.pdf'):
                if (curQueueDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                    newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
                    os.rename(QueueDir, QueueFoldersDir + newQueueName)
                    print('\n| Queue with OT/Late Orders Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
                    QueueDir = QueueDirBuilder(material, orderSize)
                    return findFullRp2EvenOrdersForPrint(QueueDir, material, orderSize, dirLookupDict['MaterialLength'][material])
                else:
                    try:
                        shutil.move(order, QueueDir)
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                    except shutil.Error:
                        shutil.copy(order, QueueDir)
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        try:
                            os.remove(order)
                        except OSError:
                            print('|> Could not remove ' + order)
                    except FileNotFoundError:
                        print('|> Couldn\'t find order to move. \n|> File: ', order)
        if (curQueueDirLength < (materialLength - 0.85)):
            for order in glob.iglob(todayOrders + 'Repeat 2/Even Panels/*.pdf'):
                if (curQueueDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                    continue
                else:
                    try:
                        shutil.move(order, QueueDir)
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                    except shutil.Error:
                        shutil.copy(order, QueueDir)
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        try:
                            os.remove(order)
                        except OSError:
                            print('|> Could not remove ' + order)
                    except FileNotFoundError:
                        print('|> Couldn\'t find order to move. \n|> File: ', order)
        if (curQueueDirLength < (materialLength - 0.85)):
            for order in glob.iglob(futureOrders + 'Repeat 2/Even Panels/*.pdf'):
                if (curQueueDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                    continue
                else:
                    try:
                        shutil.move(order, QueueDir)
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                    except shutil.Error:
                        shutil.copy(order, QueueDir)
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        try:
                            os.remove(order)
                        except OSError:
                            print('|> Could not remove ' + order)
                    except FileNotFoundError:
                        print('|> Couldn\'t find order to move. \n|> File: ', order)    
    
    newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
    print('\n| Queue Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
    os.rename(QueueDir, QueueFoldersDir + newQueueName)
    return

def findFullRp2OddOrdersForPrint(QueueDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    curQueueDirLength = 0
    oddCount = 0
    oddCountHeight = 0
    if (curQueueDirLength < (materialLength - 0.85)):
        for order in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*.pdf'):
            if (curQueueDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
                os.rename(QueueDir, QueueFoldersDir + newQueueName)
                QueueDir = QueueDirBuilder(material, orderSize)
                print('| ' + QueueDir)
                return findFullRp2OddOrdersForPrint(QueueDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                currentOrderLength = order.split('/')[11].split('-')[13]
                for orderToMatch in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*' + currentOrderLength): #don't need to include the .pdf in the filename here as it's included in currentOrderLength
                    if (curQueueDirLength + (float(order.split('/')[11].split('-')[11].split('L')[1]) + float(orderToMatch.split('/')[11].split('-')[11].split('L')[1])) - float(orderToMatch.split('/')[11].split('-')[13].split('H')[1].split('.pdf'))[0] > (materialLength * 1.01)): 
                        continue
                    else:
                        try:
                            shutil.move(order, QueueDir)
                            shutil.move(orderToMatch, QueueDir)
                        except shutil.Error:
                            shutil.copy(order, QueueDir)
                            try:
                                os.remove(order)
                            except OSError:
                                print('|> Could not remove ' + order)
                        except FileNotFoundError:
                            print('|> Couldn\'t find order to move. \n|> File: ', order)
    if (curQueueDirLength < (materialLength - 0.85)):
        for order in glob.iglob(todayOrders + 'Repeat 2/Odd Panels/*.pdf'):
            if (curQueueDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                continue
            else:
                try:
                    shutil.move(order, QueueDir)
                    if oddCount == 0:
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        oddCount = 1
                        oddCountHeight = float(order.split('/')[11].split('-')[13].split('H')[1].split('.pdf')[0])
                    else:
                        while oddCount == 1:
                            for oddOrder in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*H' + str(oddCountHeight) +'.pdf'):
                                if (curQueueDirLength + float(oddOrder.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                                    continue
                                else:
                                    shutil.move(oddOrder, QueueDir)
                                    oddCount = 0
                                    oddCountHeight = 0
                            print('| Couldn\'t find any matching, odd-paneled heights.')
                            oddCount = 0        
                except shutil.Error:
                    shutil.copy(order, QueueDir)
                    try:
                        os.remove(order)
                    except OSError:
                        print('|> Could not remove ' + order)
                except FileNotFoundError:
                    print('|> Couldn\'t find order to move. \n|> File: ', order)
    if (curQueueDirLength < (materialLength - 0.85)):
        for order in glob.iglob(futureOrders + 'Repeat 2/Odd Panels/*.pdf'):
            if (curQueueDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                continue
            else:
                try:
                    shutil.move(order, QueueDir)
                    if oddCount == 0:
                        curQueueDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        oddCount = 1
                        oddCountHeight = float(order.split('/')[11].split('-')[13].split('H')[1].split('.pdf')[0])
                    else:
                        while oddCount == 1:
                            for oddOrder in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*H' + str(oddCountHeight) +'.pdf'):
                                if (curQueueDirLength + float(oddOrder.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                                    continue
                                else:
                                    shutil.move(oddOrder, QueueDir)
                                    oddCount = 0
                                    oddCountHeight = 0
                            print('| Couldn\'t find any matching, odd-paneled heights.')
                            oddCount = 0        
                except shutil.Error:
                    shutil.copy(order, QueueDir)
                    try:
                        os.remove(order)
                    except OSError:
                        print('|> Could not remove ' + order)
                except FileNotFoundError:
                    print('|> Couldn\'t find order to move. \n|> File: ', order)

def transferFilesFromDrive():
    # Old name convention: 300014719(1)-Watercolor Herringbone-Wv-Samp-Rp 4-Qty 1-W9-H25
    # New name convention: 300013884-1-(2022-02-02)-Stnd-Wv-Samp-Rp 2-Qty 1-Watercolor Herringbone-L9.5-W25-H9
    print('\n| Checking for files in Google Drive.')
    for roots, dirs, files in os.walk(driveLocation):
        ('\n| Renaming files in Google Drive to the new naming convention.')
        for file in files:
            if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
                continue
            elif file.endswith('.pdf') != True:
                continue
            else:
                try:
                    orderNumber = file.split('(')[0]
                    orderItem = file.split('(')[1].split(')')[0]
                    templateName = file.split('-')[1]
                    material = file.split('-')[2]
                    orderSize = file.split('-')[3]
                    orderRepeat = file.split('-')[4]
                    orderQuantity = file.split('-')[5]
                    quantity = orderQuantity.split('Qty ')[1]
                    orderWidth = file.split('-')[6]
                    orderHeight = file.split('-')[7].split('.pdf')[0]
                    if orderSize == 'Samp':
                        orderWidth = 'W25'
                        orderHeight = 'H9'
                    height = orderHeight.split('H')[1]
                    orderLength = str((math.ceil(int(quantity)/2)*float(height) + ((math.floor(int(quantity)/2) * .5) + ((int(quantity) % 2) * .5))))
                except IndexError:
                    print('| Couldn\'t handle', file.split('/')[-1])
                    print('| Sorry about that.')
                    continue
            newPDFName = orderNumber + '-' + orderItem + '-(' + str(date.today()) + ')-Prty-' + material + '-' + orderSize + '-' + orderRepeat + '-' + orderQuantity + '-' + templateName + '-L' + orderLength + '-' + orderWidth + '-' + orderHeight + '.pdf'
            try:
                os.rename(driveLocation + '/' + file, driveLocation + '/' + newPDFName)
            except:
                print('\n| Trouble renaming files.\n| File:', file)
                print('\n| Returning to Main Menu. Sorry about this.')
                return main()
                
    print('| Pausing to allow name changing to update.')
    time.sleep(4)
    print('| Resuming')
    print('| Moving files from Google Drive to today\'s sorted files.')
    for roots, dirs, files in os.walk(driveLocation):
        for file in files:
            if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
                continue
            elif file.endswith('.pdf') != True:
                continue
            else:
                orderRepeat = file.split('-')[8]
                orderQuantity = int(file.split('-')[9].split('Qty ')[1])
                if orderRepeat == 'Rp 2':
                    orderRepeat = 'Repeat 2/'
                else:
                    orderRepeat = 'Repeat Non-2/'
                if orderQuantity % 2 == 0:
                    orderQuantity = 'Even Panels/'
                else:
                    orderQuantity = 'Odd Panels/'
                print('| Moving file: ', file)
                print('| Source: ', driveLocation)
                if orderSize == 'Full':
                    try:
                        shutil.move(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize]+ orderRepeat + orderQuantity)
                        time.sleep(2)
                        print('| Successfully transferred! File:', file)
                    except shutil.Error:
                        shutil.copy(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize]+ orderRepeat + orderQuantity)
                        try:
                            os.remove(driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                    except OSError as err:
                        print(err)    
                elif orderSize == 'Samp':
                    try:
                        shutil.move(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                        time.sleep(2)
                        print('| Successfully transferred! File:', file)
                    except shutil.Error:
                        shutil.copy(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                        try:
                            os.remove(driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                        except OSError as err:
                            print(err)
                    except PermissionError:
                        shutil.copy(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                        try:
                            os.remove(driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                        except OSError as err:
                            print(err)
    print('\n| Finished transferring files from Google Drive.')
    return main()

def QueueDirBuilder(material, orderSize):
    QueueDir = QueueFoldersDir + 'Queue #' + str(globalQueueCounter['QueueCounter']) + ' ' + today.strftime('%m-%d-%y') + ' ' + material + ' ' + orderSize + ' L0'
    globalQueueCounter['QueueCounter'] += 1
    #QueueDir = doesDirExist(material, orderSize)
    os.mkdir(QueueDir)
    print('| New Queue Folder: Queue #' + str(globalQueueCounter['QueueCounter']-1))
    print()
    return QueueDir

def QueueMaterialSelector():
    print('\n| Please select a material type: \n| 1. Smooth\n| 2. Woven')#\n| 3. Traditional (Don\'t.)')
    options = 1,2,3
    try:
        material = int(input('| Which material do you want to make? > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return QueueMaterialSelector()
    while int(material) not in options:
        print('\n| Not a valid choice.')
        return QueueMaterialSelector()
    if material == 1:
        return 'Smooth'
    elif material == 2:
        return 'Woven'
    elif material == 3:
        print('Traditional? No.')
        return QueueMaterialSelector()
    else:
        print('| Invalid material choice. Returning.')
        return QueueMaterialSelector()

def QueueOrderSizeSelector():
    print('\n| Please select a material size: \n| 1. Sample\n| 2. Full')
    options = 1,2
    try:
        orderSize = int(input('| Which size do you want to make? > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return QueueOrderSizeSelector()
    while int(orderSize) not in options:
        print('\n| Not a valid choice.')
        return QueueOrderSizeSelector()
    if orderSize == 1:
        return 'Sample'
    elif orderSize == 2:
        return 'Full'
    else:
        print('| Invalid size choice. Returning.')
        return QueueOrderSizeSelector()

def QueueMaterialLengthSelector():
    print('| Do you want to choose the length of material for each Queue, only the first, or consider all Queues full length? \n| 1. Each Queue\n| 2. Only the First\n| 3. All Full Length')
    options = 1,2,3
    try:
        orderSize = int(input('| Please make a selection: > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return QueueMaterialLengthSelector()
    while int(orderSize) not in options:
        print('\n| Not a valid choice.')
        return QueueMaterialLengthSelector()
    if orderSize == 1:
        orderSize = 'Each'
    elif orderSize == 2:
        orderSize = 'First'
    elif orderSize == 3:
        orderSize = 'Full'
    else:
        print('| Invalid size choice. Returning.')
        return QueueMaterialLengthSelector()

def combineQueueFoldersController(material):
    loopCounter = 0
    while loopCounter < 3:
        loopCounter += 1
        findQueueFoldersToCombine(material)
        
def getMaterialLength(material):
    try:
        materialLength = int(input('\n| Combining Full ' + material + ' Queue folders.\n| Please enter a material length > ')) * 12
        return materialLength
    except ValueError:
        print('\n| Please enter a number, not text.')
        return getMaterialLength()

def findQueueFoldersToCombine(material):
  
    materialLength = getMaterialLength(material)

    for QueueFolder in glob.iglob(QueueFoldersDir + '*' + material + ' Full*'):
        QueueLength = float(QueueFolder.split('/')[-1].split(' ')[-1].split('L')[1])
        # Checks if Queue Order Length is less that 85% of the specified Material Length
        if QueueLength < (materialLength * .85):
            # If it is less than 85%, then it begins to iterate through other Queue folders to find ones to combine.
            for QueueFolderToJoin in glob.iglob(QueueFoldersDir + '*' + material + ' Full*'):
                QueueLengthToJoin = float(QueueFolderToJoin.split('/')[-1].split(' ')[-1].split('L')[1])
                # If the Queue folder and the potential folder to join are the same folder, skips that iteration.
                if QueueFolderToJoin == QueueFolder:
                    continue
                # If the total length of the Queue folder and the potential folder to join is less than the material length, iteratethrough Queue folder to join and moves each pdf to the original folder.
                if QueueLength + QueueLengthToJoin < materialLength:
                    combineQueueFolders(QueueFolder, QueueLength, QueueFolderToJoin, QueueLengthToJoin, material)

def combineQueueFolders(QueueFolder, QueueLength, QueueFolderToJoin, QueueLengthToJoin, material):
    combinedQueueDir = QueueDirBuilder(material, 'Full')

    for printPDF in glob.iglob(QueueFolder + '/*.pdf'):
        try:
            shutil.move(printPDF, combinedQueueDir)
        except shutil.Error:
            shutil.copy(printPDF, combinedQueueDir)
            try:
                os.remove(printPDF)
            except OSError:
                print('|> Could not remove', printPDF.split('/')[-1])
    for printPDF in glob.iglob(QueueFolderToJoin + '/*.pdf'):
        try:
            shutil.move(printPDF, combinedQueueDir)
        except shutil.Error:
            shutil.copy(printPDF, combinedQueueDir)
            try:
                os.remove(printPDF)
            except OSError:
                print('|> Could not remove', printPDF.split('/')[-1])

    evenLengths = []
    #oddLengths = ()
    newQueueLength = 0

    for printPDF in glob.iglob(combinedQueueDir + '/*.pdf'):
        printPDFLength = float(printPDF.split('/')[-1].split('-')[11].split('L')[1])
        evenLengths.append(printPDFLength)

    for lengthEntry in evenLengths:
        newQueueLength += lengthEntry
    
    newQueueName = combinedQueueDir.split('/')[6].split(' L')[0] + ' L' + str(newQueueLength)
    os.rename(combinedQueueDir, QueueFoldersDir + newQueueName)
    removeEmptyQueueFolders(False)
    return combineQueueFoldersController(material)

def removeEmptyQueueFolders(safe):
    for QueueFolder in glob.iglob(QueueFoldersDir + '*'):
        QueueLength = float(QueueFolder.split('/')[-1].split(' ')[-1].split('L')[1])
        if safe == True:
            if os.path.isdir(QueueFolder) == False:
                continue
            elif (len(os.listdir(QueueFolder)) == 0) and (QueueLength == 0):
                os.rmdir(QueueFolder)
        else:
            if os.path.isdir(QueueFolder) == False:
                continue
            elif (len(os.listdir(QueueFolder)) == 0):
                os.rmdir(QueueFolder)

def findOrdersForPrint2Ptv2(QueueDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    foldersToCheck2p = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/*/*.pdf')
    curQueueDirLength = 0
    findOdd = False
    oddMatchHeight = 0
    loopCounter = 0
    while len(foldersToCheck2p) > 0:
        ### Come back to this later. For some reason, the folders to check variable doesn't update so python always evaluates it to more than 0 after it's initially created. I plugged in a loop counter to temporarily fix it.
        #foldersToCheck = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/*/*.pdf')
        while (curQueueDirLength < (materialLength - 0.9)) and loopCounter < 1:
            for order in glob.iglob(lateOrders + 'Repeat 2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curQueueDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curQueueDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
            for order in glob.iglob(todayOrders + 'Repeat 2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curQueueDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curQueueDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)        
            for order in glob.iglob(futureOrders + 'Repeat 2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curQueueDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curQueueDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
                    else:
                        try:
                            shutil.move(order, QueueDir)
                            curQueueDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                        except shutil.Error:
                            shutil.copy(order, QueueDir)
                            curQueueDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                            try:
                                os.remove(order)
                            except OSError:
                                print('|> Could not remove ' + order)
                        except FileNotFoundError:
                            print('|> Couldn\'t find order to move. \n|> File: ', order)
            loopCounter += 1
        else:
            newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
            os.rename(QueueDir, QueueFoldersDir + newQueueName)
            print('\n| Queue Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
            curQueueDirLength = 0
            QueueDir = QueueDirBuilder(material, orderSize)
            #materialLength = input('| Please input your material length. > ')
            return findOrdersForPrint2Ptv2(QueueDir, material, orderSize, int(materialLength))

def findOrdersForPrint4Ptv2(QueueDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    foldersToCheckN2p = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat Non-2/*/*.pdf')
    curQueueDirLength = 0
    findOdd = False
    oddMatchHeight = 0
    loopCounter = 0
    while len(foldersToCheckN2p) > 0:
        ### Come back to this later. For some reason, the folders to check variable doesn't update so python always evaluates it to more than 0 after it's initially created. I plugged in a loop counter to temporarily fix it.
        #foldersToCheck = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/*/*.pdf')
        while (curQueueDirLength < (materialLength - 0.9)) and loopCounter < 1:
            for order in glob.iglob(lateOrders + 'Repeat Non-2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curQueueDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curQueueDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
            for order in glob.iglob(todayOrders + 'Repeat Non-2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curQueueDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curQueueDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)        
            for order in glob.iglob(futureOrders + 'Repeat Non-2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curQueueDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curQueueDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, QueueDir)
                                curQueueDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curQueueDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, QueueDir)
                                    curQueueDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
                    else:
                        try:
                            shutil.move(order, QueueDir)
                            curQueueDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                        except shutil.Error:
                            shutil.copy(order, QueueDir)
                            curQueueDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                            try:
                                os.remove(order)
                            except OSError:
                                print('|> Could not remove ' + order)
                        except FileNotFoundError:
                            print('|> Couldn\'t find order to move. \n|> File: ', order)
            loopCounter += 1
        else:
            newQueueName = QueueDir.split('/')[6].split(' L')[0] + ' L' + str(curQueueDirLength)
            os.rename(QueueDir, QueueFoldersDir + newQueueName)
            print('\n| Queue Finished.\n| Queue Folder: ', newQueueName, '\n| Length:', str(round(curQueueDirLength/12, 2)), 'feet (' + str(curQueueDirLength), 'inches)')
            QueueDir = QueueDirBuilder(material, orderSize)
            #materialLength = input('| Please input your material length. > ')
            return findOrdersForPrint4Ptv2(QueueDir, material, orderSize, int(materialLength))

def checkRepeatSize():
    for printPDF in glob.iglob(downloadDir + '*.pdf'):
        printPDFFull = printPDF.split('/')[-1].split('-')[7]
        printPDFrepeat = int(printPDF.split('/')[-1].split('-')[8].split('Rp ')[1])
        if printPDFFull == 'Full':
            if printPDFrepeat % 2 == 1:
                try:
                    shutil.move(printPDF, needsAttention)
                    print('| File has an odd repeat and has been moved to 4 Needs Attention')
                    print('| File:', printPDF.split('/')[-1])
                except shutil.Error:
                    shutil.copy(printPDF, needsAttention)
                    try:
                        os.remove(printPDF)
                    except OSError:
                        print('|> Could not successfully remove file.')
                        print('|> File:', printPDF)
                except FileNotFoundError:
                    print('| Couldn\'t find the following file.')
                    print('| File:', printPDF)
            elif printPDFrepeat == 2:
                continue
            elif printPDFrepeat > 2:
                try:
                    cropMultiPanelPDFs(printPDF)
                except utils.PdfReadError:
                    print('| Couldn\'t crop the panels for the following order. Please check non-repeat 2 folders.')
                    continue

def cropMultiPanelPDFs(printPDFToSplit):
    orderDict = {
        'fileName':printPDFToSplit.split('.pdf')[0],
        'orderNumber': printPDFToSplit.split('/')[-1].split('-')[0],
        'orderItem': printPDFToSplit.split('-')[1],
        'orderDueDate': datetime.date(datetime.strptime(printPDFToSplit.split('(')[1].split(')')[0], '%Y-%m-%d')),
        'shipVia': printPDFToSplit.split('-')[5],
        'material': printPDFToSplit.split('-')[6],
        'orderSize': printPDFToSplit.split('-')[7],
        'repeat': int(printPDFToSplit.split('-')[8].split('Rp ')[1]),
        'repeatPanels': int(int(printPDFToSplit.split('-')[8].split('Rp ')[1]) / 2),
        'quantity': int(printPDFToSplit.split('-')[9].split('Qty ')[1]),
        'oddOrEven': int(printPDFToSplit.split('-')[9].split('Qty ')[1]) % 2,
        'templateName': printPDFToSplit.split('-')[10],
        'orderLength': float(printPDFToSplit.split('-')[11].split('L')[1]),
        'orderWidth': int(printPDFToSplit.split('-')[12].split('W')[1]),
        'orderHeight': float(printPDFToSplit.split('-')[13].split('H')[1].split('.pdf')[0]),
        'multiPagePDFs' : [],
        'PDFPanelsToCombine' : [],
        }
    
    orderDict['CroppedPDFName'] = orderDict['fileName'].split(orderDict['templateName'])[0] + orderDict['templateName'] + ' Split' + orderDict['fileName'].split(orderDict['templateName'])[1] + '.pdf'

    print('| Working file\n| ', printPDFToSplit)
    for entry in orderDict:
        print('|    ', orderDict[entry])

    os.chdir(downloadDir)
    for page in range(orderDict['repeatPanels']):
        writer = PdfFileWriter()
        inputPDF = open(printPDFToSplit,'rb')
        cropPDF = PdfFileReader(inputPDF)
        page = cropPDF.getPage(0)
        print('| File:', printPDFToSplit.split('/')[-1])
        print('| Width:', (page.mediaBox.getUpperRight_x())/72, 'inches, Height:', (page.mediaBox.getUpperRight_y()/72))
        lowerLeftX = 0
        lowerLeftY = 0
        upperRightX = 1800
        upperRightY = cropPDF.getPage(0).cropBox.getUpperRight()[1]
        for cropCount in range(orderDict['repeatPanels']):
            page.trimBox.lowerLeft = (lowerLeftX, lowerLeftY)
            page.trimBox.upperRight = (upperRightX, upperRightY)
            page.bleedBox.lowerLeft = (lowerLeftX, lowerLeftY)
            page.bleedBox.upperRight = (upperRightX, upperRightY)
            page.cropBox.lowerLeft = (lowerLeftX, lowerLeftY)
            page.cropBox.upperRight = (upperRightX, upperRightY)
            writer.addPage(page)
            lowerLeftX += 1728
            upperRightX += 1728
            printPDFName = downloadDir + orderDict['orderNumber'] + '-' + orderDict['orderItem'] + '-' + str(cropCount + 1) + '.pdf'
            if printPDFName in orderDict['multiPagePDFs']:
                continue
            else:
                orderDict['multiPagePDFs'].append(printPDFName)
            with open(printPDFName, "wb") as outputPDF:
                writer.write(outputPDF)
        inputPDF.close()

    for PDF in orderDict['multiPagePDFs']:
        writer = PdfFileWriter()
        try:
            printPDF = PdfFileReader(open(PDF, "rb"))
        except utils.PdfReadError:
            print('| Couldn\'t fix file. Skipping.\n| File:', PDF)
            continue
        numOfPages = printPDF.getNumPages()
        print('\n| File:', PDF, '\n| File has %d pages.' % printPDF.getNumPages())

        for pageNum in range(numOfPages):
            if (pageNum + 1) < numOfPages:
                continue
            else:
                writer.addPage(printPDF.getPage(pageNum))
        newNamePt1 = orderDict['fileName'].split(orderDict['templateName'])[0]
        newNamePt2 = orderDict['fileName'].split(orderDict['templateName'])[1]
        panelNum = orderDict['templateName'] + ' Panel ' + str(pageNum + 1)
        newName = newNamePt1 + panelNum + newNamePt2 + '.pdf'
        if newName in orderDict['PDFPanelsToCombine']:
            continue
        else:
            orderDict['PDFPanelsToCombine'].append(newName)

        with open(newName, 'wb') as outputPDF:
            writer.write(outputPDF)
    
    for PDF in orderDict['multiPagePDFs']:
        os.remove(PDF)
    
    print(orderDict['PDFPanelsToCombine'])

    splitAndCombinedPDF = combineSplitPDFS(orderDict['PDFPanelsToCombine'], orderDict['CroppedPDFName'])

    print('| File has been split apart, cropped, and recombined.\n| File:', splitAndCombinedPDF.split('/')[-1])

    if Path(calderaDir + '# Past Orders/Original Files/').exists() == False:
        os.mkdir(calderaDir + '# Past Orders/Original Files')
    
    storageDir = calderaDir + '# Past Orders/Original Files/'
    
    try:
        shutil.move(printPDFToSplit, storageDir)
    except shutil.Error:
        shutil.copy(printPDFToSplit, storageDir)
        os.remove(printPDFToSplit)

    for PDF in orderDict['PDFPanelsToCombine']:
        os.remove(PDF)

def combineSplitPDFS(listOfPDFs, saveLocation):
    masterPDF = PdfFileMerger()

    for PDFToMerge in listOfPDFs:
        masterPDF.append(PdfFileReader(PDFToMerge, 'rb'))
    masterPDF.write(saveLocation)

    return saveLocation

def decompress_pdf(temp_buffer):
    temp_buffer.seek(0)  # Make sure we're at the start of the file.

    process = subprocess.Popen(['pdftk.exe',
                                '-',  # Read from stdin.
                                'output',
                                '-',  # Write to stdout.
                                'uncompress'],
                                stdin=temp_buffer,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    return StringIO(stdout)

def possibleOrders(material, orderSize):
    OTOrders = glob.iglob(sortingDir + '1 - OT Orders/' + '**/*.pdf', recursive=True)
    lateOrders = glob.iglob(sortingDir + '2 - Late/' + '**/*.pdf', recursive=True)
    todayOrders = glob.iglob(sortingDir + '3 - Today/' + '**/*.pdf', recursive=True) 
    futureOrders = glob.iglob(sortingDir + '4 - Future/' + '**/*.pdf', recursive=True)
    
    possibleOrders = {
            'Order Troubles' : [],
            'Late Orders' : [],
            'Today\'s Orders' : [],
            'Future Orders' : [],
        }

    for printPDF in OTOrders:
        possibleOrders['Order Troubles'].append(printPDF)
    for printPDF in lateOrders:
        possibleOrders['Late Orders'].append(printPDF)
    for printPDF in todayOrders:
        possibleOrders['Today\'s Orders'].append(printPDF)
    for printPDF in futureOrders:
        possibleOrders['Future Orders'].append(printPDF)
            
    return possibleOrders

def buildAQueue(QueueDir, material, materialLength, orderSize):
    # OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    # lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    # todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    # futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]

    QueueLength = 0
    lengthForFull = materialLength * 0.85
    
    readyToPrint = possibleOrders(material, orderSize)
    
    for dueDate in readyToPrint:
        print('| Type:', dueDate)
        for order in readyToPrint[dueDate]:
            print('|----', order.split('/')[-1].split('-')[0], order.split('/')[-1].split('-')[7], dirLookupDict[order.split('/')[-1].split('-')[6]].split('/')[0])

    orderTroubles = readyToPrint['Order Troubles']
    lateOrders = readyToPrint['Late Orders']
    todayOrders = readyToPrint['Today\'s Orders']
    futureOrders = readyToPrint['Future Orders']

    if (len(orderTroubles) > 0) and (len(lateOrders) > 0):
        print('| Creating Queues for Order Troubles and Late Orders.')
        mainBuildQueueLoop(orderTroubles, )  




    '''
    Lets do some pseudo code!
    First, get the total length of material (let's say 150 for smooth)
    then, look for full 2' repeat orders 
    add them to the current Queue until the Queue length is 
    repeat until Queue is 85% of material length OR until there are no more full, 2' repeat orders
    once 85% of material length is exceeded, search for 13% worth of samples OR until there are no additional samples
    once that 13% has been met or exceeded, add 5% of color guides.
    Once that 5% has been met, complete the Queue.

    '''

    # findFull2pOrders()
    # findSampleOrders()
    # findColorGuides()

    return

def mainBuildQueueLoop(listOfPdfsToQueue, materialLength, lengthForFull,):
    curQueue
    
    while lengthForFull < materialLength:
        for printPDF in listOfPdfsToQueue:
            pdfName = printPDF.split('/'[-1]).split('.pdf')[0]
            pdfLength = float(pdfName.split('-')[11].split('L')[1])
            pdfOdd = int(pdfName.split('-')[9].split('Qty ')[1])
            pdfHeight = float(pdfName.split('-')[-1].split('H')[1])
            if 

startupChecks()
main()
## End