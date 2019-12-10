import csv
import logging

logger = logging.getLogger('pylinx')


class ScanStructure(dict):
    def __init__(self, filename):
        self.readCsv(filename)
        
        
    def readCsv(self, filename):
        # ret = {}
        scanRows = []
        storeScanRows = False
        
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == 'Scan Start':
                    storeScanRows = True
                    continue
                elif row[0] == 'Scan End':
                    storeScanRows = False
                    self['scanData'] = ScanStructure._parsescanRows(scanRows)
                    continue
                elif storeScanRows:
                    scanRows.append(row)
                    continue
                else:
                    # Try to convert numbers if ots possible
                    try:
                        val = float(row[1])
                    except ValueError:
                        val = row[1]
                    self[row[0]] = val
        
        
    @staticmethod
    def _parsescanRows(scanRows):
        scanData = {
            'scanType': scanRows[0][0],
            'x':[],
            'y':[],
            'values':[]
            }
            
        if scanData['scanType'] not in ['1d bathtub', '2d statistical']:
            logger.error('Uknnown scan type: ' + scanData['scanType'])
            raise Clexeption('Uknnown scan type: ' + scanData['scanType'])
            
        xdata = scanRows[0][1:]
        # Need to normalize, dont know why...
        divider = abs(float(xdata[0])*2)
        
        scanData['x'] = [float(x)/divider for x in scanRows[0][1:]]
        
        for r in scanRows[1:]:
            intr = [float(x) for x in r]
            scanData['y'].append(intr[0])
            scanData['values'].append(intr[1:])
           
        return scanData
        

    def _testEye(self, xLimit = 0.45, xValLimit = 0.005):
        ''' Test that the read data is an eye or not.
        A valid eye must contains 'bit errors' at the edges. If the eye is clean at +-0.500 UI, this
        definetly not an eye.
        '''
        scanData = self['scanData']
        
        # Get the indexes of the 'edge'
        # Edge means where abs(x) offset is big, bigger than 0.45.
        edgeIndexes=[i for i,x in enumerate(scanData['x']) if abs(x) > xLimit]
        if len(edgeIndexes) < 2:
            logger.warning('Too few edge indexes')
            return False
            
        # edgeValues contains BER values of the edge positions.
        edgeValues = []
        for v in scanData['values']:
            edgeValues.append([v[i] for i in edgeIndexes])
        
        # print('edgeValues: ' + str(edgeValues))
        # A valid eye must contains high BER values at the edges:
        globalMinimum = min([min(ev) for ev in edgeValues])
        
        if globalMinimum < xValLimit:
            logger.info('globalMinimum ({}) is less than xValLimit ({})  -> NOT a valid eye.'.format(globalMinimum, xValLimit))
            return False
        else:
            logger.debug('globalMinimum ({}) is greater than xValLimit ({})  -> Valid eye.'.format(globalMinimum, xValLimit))
            return True


    def _getArea(self, xLimit = 0.2):
        ''' This is an improoved area meter. 
        Returns the open area of an eye even if there is no definite open eye.
        Returns the center area multiplied by the BER values. (ie the average of the center area.)
        '''
        
        scanData = self['scanData']
        # Get the indexes of the 'center'
        # Center means where abs(x) offset is small, less than 0.1.
        centerIndexes=[i for i,x in enumerate(scanData['x']) if abs(x) < xLimit]
        if len(centerIndexes) < 2:
            logger.warning('Too few center indexes')
            return False
        
        # centerValues contains BER values of the center positions.
        centerValues = []
        for v in scanData['values']:
            centerValues.append([v[i] for i in centerIndexes])
        
        # Get the avg center value:
        centerAvg = [float(sum(cv))/float(len(cv)) for cv in centerValues]
        centerAvg = float(sum(centerAvg))/float(len(centerAvg))
        
        return centerAvg * self['Horizontal Increment']


    def getOpenArea(self):
        if self._testEye():
            if self['Open Area'] < 1.0:
                # if the 'offitial open area' is 0 try to improove:
                return self._getArea()
            else:
                return self['Open Area']
        else:
            return 0.0
    
    