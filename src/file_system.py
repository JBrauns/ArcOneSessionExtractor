#!/usr/bin/env python

import os
import re
import csv

def GetFileContent(rootDirectory, fileFilter, fileType, skipLines):
    result = []
    
    files = GetSelectedFiles(rootDirectory, fileFilter)
    if(fileType == 'csv'):
        for file in files:
            skipCount = skipLines
            
            rows = []
            with open(file, 'rb') as fileHandle:
                while(skipCount > 0):
                    fileHandle.next()
                    skipCount -= 1
                
                csvReader = csv.DictReader(fileHandle)
                for row in csvReader:
                    rows.append(row)
            
            result.append({ 'name': file, 'type' : fileType, 'rows' : rows })
        
    return result

def GetSelectedFiles(root, selction):
    fullPaths = []
    for path, dirs, files in os.walk(root):
        for fileName in files:
            fullPaths.append(os.path.join(path, fileName))

    reObject = re.compile(selction)
    result = filter(reObject.match, fullPaths)

    return result
