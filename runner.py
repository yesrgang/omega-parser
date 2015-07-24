# -*- coding: utf-8 -*-
import sys, time, datetime
from omega.helper import Config
from omega.log_reporter import InfluxDBLogReporter

print 'Starting...'

config = Config('config.json')
reporter = InfluxDBLogReporter(
        file_path=config['log_file_path'],
        db=config['database'])

# use last_checked from config
last_checked = config['last_checked']
if (last_checked != None):
    last_checked_time = datetime.datetime.strptime(last_checked, '%Y-%m-%dT%H:%M:%S')
    reporter.last_checked = last_checked_time

def save_last_checked_time(time):
    config['last_checked'] = time
    config.save()

while True:
    try:
        sys.stdout.write('.')
        sys.stdout.flush()

        reporter.check()
        config['last_checked'] = reporter.last_checked
        config.save()

        time.sleep(60)

    except KeyboardInterrupt:
        print 'Exiting...'
        sys.exit()

    except:
        # TODO: io error handling
        pass

