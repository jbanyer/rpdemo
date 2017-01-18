# helper methods for accessing system metrics, eg load average

from procfs import Proc

proc = Proc()

def get_loadavg():
    '''
    proc.loadavg return this:
    {'average': {1: 0.0, 5: 0.0, 15: 0.0},
     'entities': {'current': 1, 'total': 203},
      'last_pid': 2095}
    '''
    # return just the 1,5,15 load average values
    return proc.loadavg['average']
