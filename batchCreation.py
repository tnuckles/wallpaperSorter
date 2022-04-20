#!usr/bin/env python

import os, shutil, math, datetime, time, json, glob, pikepdf
import zipfile as zf
from pathlib import Path
from datetime import date, timedelta, datetime
from sqlitedict import SqliteDict
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger, utils
from io import StringIO
import subprocess