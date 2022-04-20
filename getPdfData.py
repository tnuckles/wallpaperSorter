#!usr/bin/env python
# Series of functions that break apart the name of a PDF and return a specific value

import datetime

def name(pdf):
    return pdf.split('/')[-1].split('.pdf')[0]

def friendlyName(pdf):
    friendlyPdfName = orderNumber(pdf) + ' ' +  templateName(pdf) + ' ' +  orderItem(pdf) 
    return friendlyPdfName

def orderNumber(pdf):
    return name(pdf).split('-')[0]

def orderItem(pdf):
    return name(pdf).split('-')[1]

def dueDate(pdf):
    return datetime.date(datetime.strptime(name(pdf).split('(')[1].split(')')[0], '%Y-%m-%d'))

def shipMethod(pdf):
    return name(pdf).split('-')[5]

def material(pdf):
    return name(pdf).split('-')[6]

def size(pdf):
    return name(pdf).split('-')[7]

def repeat(pdf):
    return int(name(pdf).split('-')[8].split('Rp ')[1])

def quantity(pdf):
    return int(name(pdf).split('-')[9].split('Qty ')[1])

def oddOrEven(pdf):
    return int(name(pdf).split('-')[9].split('Qty ')[1]) % 2

def templateName(pdf):
    return name(pdf).split('-')[10]

def length(pdf):
    return float(name(pdf).split('-')[11].split('L')[1])

def width(pdf):
    return int(name(pdf).split('-')[12].split('W')[1])

def height(pdf):
    return float(name(pdf).split('-')[13].split('H')[1])