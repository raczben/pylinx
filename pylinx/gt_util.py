import csv
import logging
from .util import PylinxException
from statistics import mean

logger = logging.getLogger('pylinx')


class ScanStructure(dict):
    def __init__(self, filename):
        super(ScanStructure, self).__init__()
        self.read_csv(filename)

    def read_csv(self, filename):
        # ret = {}
        scan_rows = []
        store_scan_rows = False

        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == 'Scan Start':
                    store_scan_rows = True
                    continue
                elif row[0] == 'Scan End':
                    store_scan_rows = False
                    self['scanData'] = ScanStructure._parse_scan_rows(scan_rows)
                    continue
                elif store_scan_rows:
                    scan_rows.append(row)
                    continue
                else:
                    # Try to convert numbers if ots possible
                    try:
                        val = float(row[1])
                    except ValueError:
                        val = row[1]
                    self[row[0]] = val

    @staticmethod
    def _parse_scan_rows(scan_rows):
        scan_data = {
            'scanType': scan_rows[0][0],
            'x': [],
            'y': [],
            'values': []    # type: List[List[float]]
        }

        if scan_data['scanType'] not in ['1d bathtub', '2d statistical']:
            logger.error('Unknown scan type: ' + scan_data['scanType'])
            raise PylinxException('Unknown scan type: ' + scan_data['scanType'])

        xdata = scan_rows[0][1:]
        # Need to normalize, dont know why...
        divider = abs(float(xdata[0]) * 2)

        scan_data['x'] = [float(x) / divider for x in scan_rows[0][1:]]

        for r in scan_rows[1:]:
            intr = [float(x) for x in r]
            scan_data['y'].append(intr[0])
            scan_data['values'].append(intr[1:])

        return scan_data

    def _test_eye(self, x_limit=0.45, x_val_limit=0.005):
        """ Test that the read data is an eye or not.
        A valid eye must contains 'bit errors' at the edges. If the eye is clean at +-0.500 UI, this
        definitely not an eye.
        """
        scan_data = self['scanData']

        # Get the indexes of the 'edge'
        # Edge means where abs(x) offset is big, bigger than x_limit=0.45.
        edge_indexes = [i for i, x in enumerate(scan_data['x']) if abs(x) > x_limit]
        logger.debug(edge_indexes)
        if len(edge_indexes) < 2:
            logger.warning('Too few edge indexes')
            return False

        # edge_values contains BER values of the edge positions.
        edge_values = []
        for v in scan_data['values']:
            edge_values.append([v[i] for i in edge_indexes])

        # print('edgeValues: ' + str(edgeValues))
        # A valid eye must contains high BER values at the edges:
        global_minimum = min([min(ev) for ev in edge_values])

        if global_minimum < x_val_limit:
            logger.info(
                'globalMinimum ({}) is less than x_val_limit ({})  -> NOT a valid eye.'.format(
                    global_minimum, x_val_limit))
            return False
        else:
            logger.debug(
                'global_minimum ({}) is greater than x_val_limit ({})  -> Valid eye.'.format(
                    global_minimum, x_val_limit))
            return True

    def _get_area(self, x_limit=0.2):
        """ This is an improved area meter.
        Returns the open area of an eye even if there is no definite open eye.
        Returns the center area multiplied by the BER values. (ie the average of the center area.)
        """

        scan_data = self['scanData']
        # Get the indexes of the 'center'
        # Center means where abs(x) offset is small, less than 0.1.
        center_indexes = [i for i, x in enumerate(scan_data['x']) if abs(x) < x_limit]
        if len(center_indexes) < 2:
            logger.warning('Too few center indexes')
            return False

        # centerValues contains BER values of the center positions.
        center_values = []
        for v in scan_data['values']:
            center_values.append([v[i] for i in center_indexes])

        # Get the avg center value:
        center_avg = [0.1 / float(sum(cv)) / float(len(cv)) for cv in center_values]
        center_avg = mean(center_avg)

        return center_avg * self['Horizontal Increment']

    def get_open_area(self):
        if self._test_eye():
            if self['Open Area'] < 1.0:
                # if the 'official open area' is 0 try to improve:
                return self._get_area()
            else:
                return self['Open Area']
        else:
            return 0.0
