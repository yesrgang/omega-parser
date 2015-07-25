# -*- coding: utf-8 -*-
import re, pytz, datetime, os.path
from influxdb import InfluxDBClient

def utc_iso_string(dt):
    # hard coded for now ...
    local_tz = pytz.timezone('America/Denver')
    return local_tz.localize(dt).astimezone(pytz.utc)

class DataPoint(object):
    def __init__(self, reading_line):
        components = reading_line.split(',')
        data = {
            'time':    components[1],
            'temperature': components[2],
            'humidity':    components[4],
            'pressure':    components[6]
        }

        # Temperature (°C), Humidity (%RH), Absolute Pressure (PSIA)
        for prop in ['temperature', 'humidity', 'pressure']:
            match = re.search('^"\+?([^\+"]*)"$', data[prop])
            try:
                data[prop] = float(match.group(1))
            except:
                data[prop] = 0

        # DateTime (YYYY-MM-DD HH:MM:SS)
        data['time'] = datetime.datetime.strptime(data['time'][1:-1], '%Y-%m-%d %H:%M:%S')

        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def to_influxdb(self):
        measurements = []

        for kind in ['temperature', 'humidity', 'pressure']:
            measurements.append({
                'measurement': 'environment',
                'tags': {
                    'type': kind
                },
                'time': utc_iso_string(self['time']).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'fields': {
                    'value': self[kind]
                }
            })

        return measurements

class LogReporter(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.watch_thread = None
        self.last_checked = datetime.datetime.fromtimestamp(0)

    def check(self, callback=None):
        mtime = os.path.getmtime(self.file_path)
        mtime = datetime.datetime.fromtimestamp(mtime)

        count = 0
        if (self.last_checked < mtime):
            count = self.read(callback)

        self.last_checked = mtime

        return count

    def read(self, callback=None):
        count = 0

        f = open(self.file_path, 'rb')

        # seek EOF
        f.seek(0, 2)

        # seek EOF-1 or 0 (empty file)
        f.seek(max(f.tell() - 1, 0))

        while True:
            l = ''

            # break if begin of file reached
            if (f.tell() < 1): break

            while True:
                c = f.read(1)
                f.seek(f.tell() - 2)

                if (c == '\n' or f.tell() < 1): break
                l += c

            # skip empty lines
            if (len(l) == 0): continue

            # reverse line (read in backwards)
            l = l[::-1]

            # break if header of file is reached
            if (l[0] == '#'): break

            # create data point and process data
            p = DataPoint(l)

            if (self.last_checked < p['time']):
                self.process(p)
                count += 1

                # call callback if given
                if callback: callback(p)

            else:
                break

        return count

    def process(self, p):
        return

class InfluxDBLogReporter(LogReporter):
    def __init__(self, file_path='', db=''):
        self.db_client = InfluxDBClient.from_DSN(db)
        super(InfluxDBLogReporter, self).__init__(file_path)

    def process(self, p):
        client = self.db_client
        client.write_points(p.to_influxdb())
