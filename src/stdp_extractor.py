import re
import argparse
import math
import os, sys

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

def plotToImage(x, y, path, fileName, **kwargs):
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
        fileFormat = 'svg'
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
            if(key == 'format'):
                fileFormat = value

        pyPlot.plot(xPy, yPy, lineStyle)
        # pyPlot.ylim((-0.15, 0.15))
        pyPlot.grid(linestyle='dotted')
        # pyPlot.yticks(numpy.arange(-0.15, 0.15, step=0.1))

        totalPath = ".".join((os.path.join(os.path.abspath(path), fileName), fileFormat))
        # pyPlot.gca().set_position([0, 0, 1, 1])
        pyPlot.savefig(totalPath, format=fileFormat)

class enum :
    def __init__(self, attributes):
        attributeIndex = int(0)
        for attribute in attributes:
            setattr(self, attribute, attributeIndex)
            attributeIndex += 1

stdp_data_e = enum(['wordline',
                    'bitline',
                    'resistance',
                    'amplitude',
                    'pulsewidth',
                    'tag',
                    'readtag',
                    'readvoltage'])

def get_file_content(path):
    with open(path, "r") as src:
        result = src.readlines()

    return(result)

def write_file_content(path, content):
    with open(path, "w") as dest:
        dest.write(content)

parser = argparse.ArgumentParser(description="STDP extracter")
parser.add_argument("-d", dest="dest", help="Destination of extraction")
parser.add_argument("-s", dest="src", help="Source of stdp data")

args = parser.parse_args()

print("Args: src=%s\ndest=%s" % (args.src, args.dest))
fileContent = get_file_content(args.src)

def getStdpBlock(data, rowEntries, rowEntriesLast):
    result = {'dt':None, 'r0':None, 'r1':None, 'a':None, 'pw':None}

    result['r0'] = rowEntries[stdp_data_e.resistance]
    result['r1'] = rowEntriesLast[stdp_data_e.resistance]

    result['a'] = rowEntries[stdp_data_e.amplitude]
    result['pw'] = rowEntries[stdp_data_e.pulsewidth]

    groups = re.findall("(-?\\d+.\\d+)", rowEntries[stdp_data_e.tag])
    assert (len(groups) == 1), "Unexpected ammount of deltas found: %d" % len(groups)
    for group in groups:
        result['dt'] = float(group)

    data.append(result)
        
class stdp_block:
    def __init__(self):
        self.begin = {'wl':0, 'bl':0, 'rv':0}
        self.end = {}
        self.data = []

def floatInRange(value):
    result = (value != float('+inf')) and (value != float('-inf')) and (value != float('nan'))
    return result
        
stdpSetIndex = 0
stdpSets = [stdp_block()]

inStdpBlock = False
lineIndex = 0
rowEntriesLast = None
for line in fileContent:
    rowEntries = line.split(",")
    
    tag = ""
    if(len(rowEntries) > stdp_data_e.tag):
        tag = rowEntries[stdp_data_e.tag]

    if(tag == "stdp_e"):
        inStdpBlock = False
        stdpSets[stdpSetIndex].end = ()
        stdpSetIndex += 1
        
        stdpSets.append(stdp_block())
    elif((tag == "stdp_s") or inStdpBlock):
        stdpSets[stdpSetIndex].begin['wl'] = rowEntries[stdp_data_e.wordline]
        stdpSets[stdpSetIndex].begin['bl'] = rowEntries[stdp_data_e.bitline]
        stdpSets[stdpSetIndex].begin['rv'] = rowEntries[stdp_data_e.readvoltage]
        if(inStdpBlock):
            if(re.search("(after)", rowEntries[stdp_data_e.tag].strip())):
                getStdpBlock(stdpSets[stdpSetIndex].data, rowEntries, rowEntriesLast)
                
        inStdpBlock = True

    lineIndex += 1
    rowEntriesLast = rowEntries

stdpSetIndex = 0
for stdpSet in stdpSets:
    # print("STDP_SET: %d" % stdpSetIndex)
    sortedData = sorted(stdpSet.data, key=lambda k: k['dt'])

    csvContent = ""
    dtData = []
    valuesY = []
    dataSetIndex = 0
    for dataSet in sortedData:
        r0 = float(dataSet['r0'])
        r1 = float(dataSet['r1'])
        if(floatInRange(r0) and floatInRange(r1) and (r0 != r1)):
            xValue = float(dataSet['dt']) * (1000**2)
            dtData.append(xValue)
            
            valueSign = -1 if (r1 > r0) else 1
            valueMax = max(r0, r1)
            valueMin = min(r0, r1)
            valueNorm = valueMin
            valueDelta = (valueMax - valueMin)
            yValue = (valueDelta / valueNorm)*valueSign
            valuesY.append(yValue)

            csvContent += ";".join((str(xValue), str(yValue), "\n"))

    print("Plot image number \"%d\"" % (stdpSetIndex))
    fileFormats = ['svg', 'png']
    for fileFormat in fileFormats:
        plotToImage(dtData, valuesY, "..\\img", "test_"+str(stdpSetIndex),
                    title="STDP Set "+str(stdpSetIndex)+";Probe C3_3.5k$\Omega$", ylabel=r'$\Delta G/G_0$',
                    xlabel=r'$\Delta t (\mu s)$', format=fileFormat)
    pathOut = os.path.abspath("..\img") + "\\test_{0}.csv".format(stdpSetIndex) 
    write_file_content(pathOut, csvContent)
    
    stdpSetIndex +=1
    
#for block_index in range(0, len(stdp_blocks)):
#    path_out = args.dest.replace(".csv", ("_" + str(block_index) + ".csv"))
#    write_file_content(path_out, stdp_blocks[block_index].format_content(";", False))
#    print("File %s written!" % path_out)

