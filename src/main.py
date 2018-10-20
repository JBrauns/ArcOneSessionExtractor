import json
import os
import sys

matplotlibFound = False
try:
    import matplotlib
    matplotlibFound = True
except ImportError:
    print("Matplotlib not found on this system")

numpyFound = False
try:
    import numpy
    numpyFound = True
except ImportError:
    print("Numpy not found on this system")

if(matplotlibFound and numpyFound):
    import matplotlib.pyplot as pyPlot

import arc_parser as arcp
import file_system as fsys

rootPath = "C:/Users/Joshi/Documents/GitHub/ArcOneSessionExtractor/stdp"
imgPath = "C:/Users/Joshi/Documents/GitHub/ArcOneSessionExtractor/img"
fileFilter = r'.*trace_[0-9]+_.*'

def PlotToImage(x, y, path, fileName, fileFormat, **kwargs):
    if(not(matplotlibFound and numpyFound)):
        print("Can't plotToImage for %s" % (fileName))
        return
    else:
        factor = 0.7
        fig = pyPlot.figure(figsize=[14*factor, 8.65*factor])

        xPy = numpy.asarray(x)
        yPy = numpy.asarray(y)

        gridOn = False
        lineStyle = '.'
        for(key, value) in kwargs.items():
            if(key == 'title'):
                pyPlot.title(kwargs['title'])
            if(key == 'ylabel'):
                pyPlot.ylabel(kwargs['ylabel'])
            if(key == 'xlabel'):
                pyPlot.xlabel(kwargs['xlabel'])
            if(key == 'grid_on'):
                gridOn = True
            if(key == 'line_style'):
                lineStyle = value

        pyPlot.plot(xPy, yPy, lineStyle)
        # pyPlot.ylim((-0.15, 0.15))
        pyPlot.grid(linestyle='dotted')
        # pyPlot.yticks(numpy.arange(-0.15, 0.15, step=0.1))

        totalPath = ".".join((os.path.join(os.path.abspath(path), fileName), fileFormat))
        # pyPlot.gca().set_position([0, 0, 1, 1])
        pyPlot.savefig(totalPath, format=fileFormat)
        pyPlot.close('all')

jsonDump = {}
globalFileIndex = 0
logFile = open('log.json', 'w')
fileContents = fsys.GetFileContent(rootPath, fileFilter, 'csv', 2)
for fileContent in fileContents:
    arcElements = arcp.GetArcElements(fileContent, logFile)

    jsonObject = { 'RowCount' : len(fileContent['rows']), 'Elements' : [] }
    lastRetentionObject = None
    fileIndex = 0
    for arcElement in arcElements:
        if(arcElement.Type == arcp.ArcElementType.Retention):
            jsonObject['Elements'].append({ 'Type' : 'Retention', 'Count' : arcElement.Count, 'AvgR' : arcElement.GetAvgResistance() })
            lastRetentionObject = arcElement
        elif(arcElement.Type == arcp.ArcElementType.STDP):
            dt, rnom = arcElement.GetDtRnomSorted()
            jsonObject['Elements'].append({ 'Type' : 'STDP', 'RStart' : arcElement.RStart, 'REnd' : arcElement.REnd, 'DT' : dt, 'RNom' : rnom })

            retAvgR = 0.0
            if(not (lastRetentionObject is None)):
                retAvgR = lastRetentionObject.GetAvgResistance()

            plotTitle = "R_{stdp,s}=%16.2f R_{ret}=%16.2f" % (arcElement.RStart, retAvgR)
            PlotToImage(dt, rnom, imgPath, 'img_%d' % (globalFileIndex), 'png', title=plotTitle)
            head, tail = os.path.split(fileContent['name'])
            sys.stdout.write('\r%s Index=%d Title=%s' % (tail, fileIndex, plotTitle))
            sys.stdout.flush()

            lastRetentionObject = None
            fileIndex += 1
            globalFileIndex += 1
        else:
            lastRetentionObject = None
            
    print('\n')
    jsonDump[fileContent['name']] = jsonObject

print >> logFile, json.dumps(jsonDump, sort_keys=True, indent=2)

logFile.close()
