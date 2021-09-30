# weewx-aqi
# Copyright 2018 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

from setup import ExtensionInstaller

def loader():
    return AirQualityIndexInstaller()

class AirQualityIndexInstaller(ExtensionInstaller):
    def __init__(self):
        super(AirQualityIndexInstaller, self).__init__(
            version="1.4",
            name='aqi',
            description='Calculates air quality indexes.',
            author="Jonathan Koren",
            author_email="jonathan@jonathankoren.com",
            process_services='user.aqi.service.AqiService',
            config={
                'AqiService': {
                    'standard': {
                        'data_binding': 'aqi_binding',
                        'standard': 'user.aqi.us.NowCast',
                    },
                    'air_sensor': {
                        'data_binding': 'purpleair_binding',
                        'usUnits': 'usUnits',
                        'dateTime': 'dateTime',
                        'temp': 'purple_temperature',
                        'pressure': 'purple_pressure',
                        'pm2_5': 'pm2_5_atm',
                        'pm10_0': 'pm10_0_atm',
                    },
                },
                'DataBindings': {
                    'aqi_binding': {
                        'database': 'aqi_sqlite',
                        'table_name': 'archive',
                        'manager': 'weewx.manager.DaySummaryManager',
                        'schema': 'user.aqi.service.schema'}},
                'Databases': {
                    'aqi_sqlite': {
                        'database_name': 'aqi.sdb',
                        'driver': 'weedb.sqlite'}},
            },
            files=[('bin/user',
                    [ 'bin/user/aqi/__init__.py',
                    'bin/user/aqi/au.py',
                    'bin/user/aqi/ca.py',
                    'bin/user/aqi/calculators.py',
                    'bin/user/aqi/eu.py',
                    'bin/user/aqi/india.py',
                    'bin/user/aqi/mx.py',
                    'bin/user/aqi/service.py',
                    'bin/user/aqi/standards.py',
                    'bin/user/aqi/uk.py',
                    'bin/user/aqi/units.py',
                    'bin/user/aqi/us.py' ]),
                ('bin',
                    [ 'bin/aqi_backfill' ])
            ]
        )
