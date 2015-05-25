#!/usr/bin/env python

import logging
import os
import platform
import re
import time

import serial

log = logging.getLogger(__name__)

data_line_regex = re.compile(
    '[0-9]-[0-9]:(?P<attr>[0-9\.]+)\((?P<value>[0-9A-F\.]+?)\*?(?P<unit>kWh?)?\)'
    '|\((?P<gas>[0-9\.]+)\)'
)

attr_lookup = {
    '96.1.1': 'meter_id',
    '1.8.1': 'afgenomen_dal',
    '1.8.2': 'afgenomen_piek',
    '2.8.1': 'teruggeleverd_dal',
    '2.8.2': 'teruggeleverd_piek',
    '96.14.0': 'daltarief',
    '1.7.0': 'huidig_verbruik',
    '2.7.0': 'huidig_teruggeleverd',
    '96.3.10': 'stand_schakelaar',
    '24.1.0': 'apparaten_op_mbus',
    '96.1.0': 'gas_meter_id',
    '24.3.0': 'gas_meettijd',
    '24.4.0': 'stand_gasklep',
    '': 'gas',
}

logging.basicConfig(level=logging.DEBUG)

node = platform.node()

def readpacket(tty):
    """Read one 'packet' of meter statistics data."""
    ser = serial.Serial(tty, 9600, bytesize=7, parity='E', stopbits=1, timeout=2)

    packet = False
    log.info('start read')

    data = ser.read(1024)
    log.debug('data in: %s', data)

    lines = []
    for line in data.splitlines():
        if not line:
            continue

        if line.startswith('/'):
            log.debug('packet start')
            packet = True
            lines = []

        if packet:
            lines.append(line)

        if packet and line == '!':
            log.debug('packet end')
            ser.close()
            return lines

    ser.close()
    return []

def parse(datalines):
    """Convert smart meter statistics to dictionary."""
    metrics = {}

    for line in datalines:
        m = data_line_regex.search(line)
        if m:
            attr, value, unit, gas = m.groups()

            if gas:
                metrics['gas'] = gas
                continue

            attr_name = attr_lookup.get(attr)
            if attr_name:
                metrics[attr_name] = value

    return metrics

def stats(metrics, graphite_prefix, now):
    """Print metrics in graphite compatible format."""
    meter_id = metrics.pop('meter_id')
    gas_meter_id = metrics.pop('gas_meter_id')

    def send_metric(device, metric, value):
        msg = '%s %s %s' % ('.'.join([graphite_prefix, 'meters', metric]), str(value), now)
        print(msg)

    for name, value in metrics.items():
        if name.startswith('gas'):
            send_metric(gas_meter_id, name, value)
        else:
            send_metric(meter_id, name, value)

def main():
    tty = os.environ.get('SMARTMETER_TTY', '/dev/ttyUSB0')
    graphite_prefix = os.environ.get('GRAPHITE_PREFIX', '')

    while True:
        datalines = readpacket(tty)
        if datalines:
            metrics = parse(datalines)

            now = int(time.time())
            stats(metrics, graphite_prefix, now)

if __name__ == '__main__':
    main()
