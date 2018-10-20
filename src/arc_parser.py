#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import re

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

ArcRowElements = enum('Wordline', 'Bitline', 'Resistance', 'Amplitude', 'PulseWidth', 'Tag', 'ReadTag', 'ReadVoltage')
ArcElementType = enum('Retention', 'STDP')

class ArcElement(object):
    def __init__(self, arcType):
        self.Type = arcType
        self.Count = 0
        
        self.SetDataContainter(ArcRowElements.Wordline)
        self.SetDataContainter(ArcRowElements.Bitline)
        self.SetDataContainter(ArcRowElements.Amplitude)
        self.SetDataContainter(ArcRowElements.PulseWidth)
        self.SetDataContainter(ArcRowElements.Tag)
        self.SetDataContainter(ArcRowElements.ReadTag)
        self.SetDataContainter(ArcRowElements.ReadVoltage)

    def SetDataContainter(self, index):
        setattr(self, '__dat_container_%s' % str(index), [])
        
    def GetDataContainer(self, index):
        result = getattr(self, '__dat_container_%s' % str(index))
        return result
        
    def AddDataByIndex(self, row, index):
        self.GetDataContainer(index).append(GetArcRowElement(row, index))

    def AddDataByValue(self, row, index, value):
        self.GetDataContainer(index).append(value)
        
class ArcRetention(ArcElement):
    def __init__(self):
        super(ArcRetention, self).__init__(ArcElementType.Retention)
        self.SetDataContainter('r')

    def Add(self, row):
        r = float(GetArcRowElement(row, ArcRowElements.Resistance))
        if((not math.isnan(r)) and (not math.isinf(r))):
            self.Count += 1
        self.AddDataByIndex(row, ArcRowElements.Bitline)
        self.AddDataByIndex(row, ArcRowElements.Wordline)
        self.AddDataByValue(row, 'r', r)
        
    def GetAvgResistance(self):
        result = 0.0
        for r in self.GetDataContainer('r'):
            if((not math.isnan(r)) and (not math.isinf(r))):
                result += r / self.Count
            
        return result

class ArcSTDP(ArcElement):
    def __init__(self):
        super(ArcSTDP, self).__init__(ArcElementType.STDP)
        
        self.SetDataContainter('dt')
        self.SetDataContainter('rnom')
        self.RNorm = 0.0
        
        self.MatchBefore = re.compile(r'stdp dt.*before')
        self.MatchAfter = re.compile(r'stdp dt.*after')
        
        self.RStart = -1.0
        self.REnd = -1.0

    def GetDtRnomTuple(self):
        dt = self.GetDataContainer('dt')
        rnom = self.GetDataContainer('rnom')
        return(dt, rnom)

    def GetDtRnomSorted(self):
        dt, rnom = self.GetDtRnomTuple()
        dt, rnom = zip(*sorted(zip(dt, rnom)))
        return(dt, rnom)
        
    def Add(self, row):
        tag = GetArcRowElement(row, ArcRowElements.Tag)
        if(tag == 'stdp_s'):
            self.RStart = float(GetArcRowElement(row, ArcRowElements.Resistance))
        elif(tag == 'stdp_e'):
            self.REnd = float(GetArcRowElement(row, ArcRowElements.Resistance))
        else:
            if(self.MatchBefore.match(tag)):
                self.RNorm = float(GetArcRowElement(row, ArcRowElements.Resistance))
            elif(self.MatchAfter.match(tag)):
                group = re.findall(r'(-?[0-9]+.[0-9]+)', tag)
                dt = float(group[0])
                thisR = float(GetArcRowElement(row, ArcRowElements.Resistance))

                if((not math.isinf(self.RNorm)) and (not math.isinf(thisR))):
                    rdiff = abs(self.RNorm - thisR)
                    rnom = rdiff / self.RNorm
                    
                    self.AddDataByValue(row, 'dt', dt)
                    self.AddDataByValue(row, 'rnom', rnom)
                    
def GetArcElements(fileContent, logFile):
    rowIndex = 0

    inElement = False

    isError = False
    result = []
    element = None
    for row in fileContent['rows']:
        if(len(row) >= 8):
            if(inElement):
                element.Add(row)
            
            if('RET_s' == row['Tag']):
                element = ArcRetention()
                inElement = True
                element.Add(row)
            elif('RET_e' == row['Tag']):
                inElement = False
                element.Add(row)
                result.append(element)
            
            elif('stdp_s' == row['Tag']):
                element = ArcSTDP()
                inElement = True
                element.Add(row)
            elif('stdp_e' == row['Tag']):
                inElement = False
                element.Add(row)
                result.append(element)
            else:
                # print >> logFile, "unknown Tag: %s" % (row['Tag'])
                pass
                
            rowIndex += 1
        else:
            if(not isError):
                isError = True
                print >> logFile, "Incorrect Lenght=%d row=%s" % (len(row), ', '.join(row))
            
    return result
        
def GetArcRowElement(row, identifier):
    result = ''
    if(identifier == ArcRowElements.Wordline):
        result = row['Wordline']
    elif(identifier == ArcRowElements.Bitline):
        result = row['Bitline']
    elif(identifier == ArcRowElements.Resistance):
        result = row['Resistance']
    elif(identifier == ArcRowElements.Tag):
        result = row['Tag']
    return result
