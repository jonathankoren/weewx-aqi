# weewx-aqi
# Copyright 2018-2021 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

import sys
import syslog
import time

import weeutil.weeutil
import weewx
import weewx.cheetahgenerator
import weewx.engine
import weewx.units

from . import calculators
from . import standards
from . import units

schema = [
    ('dateTime', 'INTEGER NOT NULL PRIMARY KEY'),
    ('interval', 'INTEGER NOT NULL'),
    ('usUnits', 'INTEGER NOT NULL'),
    ('aqi_standard', 'INTEGER NOT NULL'),
    ('aqi_composite', 'REAL'),
    ('aqi_composite_category', 'INTEGER'),
    ('aqi_pm2_5', 'REAL'),
    ('aqi_pm2_5_category', 'INTEGER'),
    ('aqi_pm10_0', 'REAL'),
    ('aqi_pm10_0_category', 'INTEGER'),
    ('aqi_co', 'REAL'),
    ('aqi_co_category', 'INTEGER'),
    ('aqi_no2', 'REAL'),
    ('aqi_no2_category', 'INTEGER'),
    ('aqi_so2', 'REAL'),
    ('aqi_so2_category', 'INTEGER'),
    ('aqi_o3', 'REAL'),
    ('aqi_o3_category', 'INTEGER'),
    ('aqi_nh3', 'REAL'),
    ('aqi_nh3_category', 'INTEGER'),
    ('aqi_pb', 'REAL'),
    ('aqi_pb_category', 'INTEGER'),
]

def _trim_dict(d):
    '''Removes all entries in the dict where value is None.'''
    for (k, v) in list(d.items()):
        if v is None:
            d.pop(k)
    return d

def _make_dict(row, colnames):
    if type(row) == dict:
        return row
    d = {}
    for i in range(len(row)):
        d[colnames[i]] = row[i]
    return d

def get_unit_from_column(obs_column, usUnits):
    pollutant_group = weewx.units.obs_group_dict.get(obs_column)
    obs_unit = None
    if usUnits == weewx.US:
        obs_unit = weewx.units.USUnits[pollutant_group]
    elif usUnits == weewx.METRIC:
        obs_unit = weewx.units.MetricUnits[pollutant_group]
    elif usUnits == weewx.METRICWX:
        obs_unit = weewx.units.MetricWXUnits[pollutant_group]
    return obs_unit


class AqiService(weewx.engine.StdService):
    '''
    [AqiService]
        [standard]
        data_binding = aqi_binding       -- Required
        standard = user.aqi.us.NowCast   -- Required.

        [air_sensor]                     -- Required.
        data_binding = purpleair_binding -- Required.
        usUnits = usUnits                -- Optional. Column indicating the data's units. Default: usUnits
        dateTime = dateTime              -- Optional. Column in sensor_data_binding indicating when the reading was taken in epoch seconds. Default: dateTime
        temp = purple_temperature        -- Optional. Suggested if sensor measures temperature. Column in sensor_data_binding of air temperature. Default: reads from wx_archive.
        pressure = purple_pressure       -- Optional. Suggested if sensor measures air pressure. Column in sensor_data_binding of air pressure. Default: reads from wx_archive.
        pm2_5 = pm2_5_atm                -- Optional. Column in sensor_data_binding measuring fine particulate matter <= 2.5 micrometers in width.
        pm10_0 = pm10_0_atm              -- Optional. Column in sensor_data_binding measuring particulate matter <= 10 micrometers in width.
        co =                             -- Optional. Column in sensor_data_binding measuring carbon monoxide concentrations.
        no2 =                            -- Optional. Column in sensor_data_binding measuring nitrogen dioxide concentrations.
        so2 =                            -- Optional. Column in sensor_data_binding measuring sulfur monoxide concentrations.
        o3 =                             -- Optional. Column in sensor_data_binding measuring ozone concentrations.
        nh3 =                            -- Optional. Column in sensor_data_binding measuring ammonia concentrations.
        pb =                             -- Optional. Column in sensor_data_binding measuring lead concentrations.
    '''
    def __init__(self, engine, config_dict):
        super(AqiService, self).__init__(engine, config_dict)

        # configure the aqi standard
        standard_config_dict = config_dict['AqiService']['standard']
        fq_standard = standard_config_dict['standard']
        standard_path = '.'.join(fq_standard.split('.')[:-1])
        standard_name = fq_standard.split('.')[-1]
        __import__(standard_path)
        standard_class = getattr(sys.modules[standard_path], standard_name)
        self.aqi_standard = standard_class(int(config_dict['StdArchive']['archive_interval']))

        # open the aqi data store
        aqi_data_binding_name = standard_config_dict['data_binding']
        self.aqi_dbm = self.engine.db_binder.get_manager(data_binding=aqi_data_binding_name, initialize=True)

        # confirm aqi schema
        dbcols = self.aqi_dbm.connection.columnsOf(self.aqi_dbm.table_name)
        dbm_dict = weewx.manager.get_manager_dict(
            config_dict['DataBindings'],
            config_dict['Databases'],
            aqi_data_binding_name)
        memcols = [x[0] for x in dbm_dict['schema']]
        if dbcols != memcols:
            raise Exception('aqi store schema mismatch: %s != %s' % (dbcols, memcols))

        # configure the sensor readings
        sensor_config_dict = config_dict['AqiService']['air_sensor']
        self.sensor_units_column = sensor_config_dict.get('usUnits', 'usUnits')
        self.sensor_epoch_seconds_column = sensor_config_dict.get('dateTime', 'dateTime')
        self.sensor_temp_column = sensor_config_dict.get('temp', None)
        self.sensor_pressure_column = sensor_config_dict.get('pressure', None)
        self.sensor_pm2_5_column = sensor_config_dict.get('pm2_5', None)
        self.sensor_pm10_0_column = sensor_config_dict.get('pm10_0', None)
        self.sensor_co_column = sensor_config_dict.get('co', None)
        self.sensor_no2_column = sensor_config_dict.get('no2', None)
        self.sensor_so2_column = sensor_config_dict.get('so2', None)
        self.sensor_o3_column = sensor_config_dict.get('o3', None)
        self.sensor_nh3_column = sensor_config_dict.get('nh3', None)
        self.sensor_pb_column = sensor_config_dict.get('pb', None)
        self.sensor_dbm = self.engine.db_binder.get_manager(data_binding=sensor_config_dict['data_binding'], initialize=True)

        # configure the main weather sensor if needed
        self.use_weather_temp = (self.sensor_temp_column is None)
        self.use_weather_pressure = (self.sensor_pressure_column is None)
        self.weather_us_units = weewx.units.unit_constants[config_dict['StdConvert']['target_unit']]
        self.weather_dbm = self.engine.db_binder.get_manager()

        # confirm the sensor schema
        dbcols_set = set(self.sensor_dbm.connection.columnsOf(self.sensor_dbm.table_name))
        for needle in list(self._get_polution_sensor_columns().values()):
            if (needle != None) and (needle not in dbcols_set):
                raise Exception('air sensor schema mismatch. %s not found in %s' % (needle, dbcols_set))


        # listen for NEW_ARCHIVE_RECORDS
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

    def _get_polution_sensor_columns(self):
        '''Returns a mapping from canonical to configured column names. If a
        column is not configured it will not be in the map.'''
        return _trim_dict({
            'dateTime': self.sensor_epoch_seconds_column,
            'usUnits': self.sensor_units_column,
            calculators.PM2_5: self.sensor_pm2_5_column,
            calculators.PM10_0: self.sensor_pm10_0_column,
            calculators.CO: self.sensor_co_column,
            calculators.NO2: self.sensor_no2_column,
            calculators.SO2: self.sensor_so2_column,
            calculators.O3: self.sensor_o3_column,
            calculators.NH3: self.sensor_nh3_column,
            calculators.PB: self.sensor_pb_column,
        })

    def _get_weather_sensor_columns(self):
        '''Returns the epoch second column, followed by the temperature and
        pressure readings from the air pollution sensor.'''
        return _trim_dict({
            'dateTime': self.sensor_epoch_seconds_column,
            'weather_usUnits': self.sensor_units_column,
            'outTemp': self.sensor_temp_column,
            'pressure': self.sensor_pressure_column,
        })

    def _join_sensor_results(self, pollutant_observations, pollutant_cols, weather_observations, weather_cols, epsilon):
        '''Returns an array containing the join of the pollutant and weather
        observations. All joined observations must have occured within epsilon
        seconds of each other.'''
        joined = []
        try:
            po = _make_dict(next(pollutant_observations), pollutant_cols)
            wo = _make_dict(next(weather_observations), weather_cols)
            while True:
                delta = po['dateTime'] - wo['dateTime']
                if abs(delta) < epsilon:
                    # close enough.
                    d = dict.copy(po)
                    for (k, v) in list(wo.items()):
                        if k not in d or d[k] is None:
                            d[k] = v
                    joined.append(d)
                    po = _make_dict(next(pollutant_observations), pollutant_cols)
                    wo = _make_dict(next(weather_observations), weather_cols)
                elif delta > 0:
                    # pollutant is future, increment weather
                    wo = _make_dict(next(weather_observations), weather_cols)
                else:
                    # Weather is future, increment pollutant
                    po = _make_dict(next(pollutant_observations), pollutant_cols)
        except StopIteration:
            pass

        return joined

    def shutDown(self):
        '''Service is shutting down.'''
        try:
            self.aqi_dbm.close()
        except:
            pass
        try:
            self.sensor_dbm.close()
        except:
            pass

    def new_archive_record(self, event):
        '''This event is triggered when a new archive is ready from the main
        weather sensor. PurpleAir (and presumably other air sensor plugins) uses
        this event to query air sensor. This has the added benefit of
        (approximately) syncing the readings from weather and air quality
        sensors.'''
        max_time_difference = event.record['interval'] * 60
        now = event.record['dateTime']
        start_time = now - self.aqi_standard.max_duration()
        end_time = now - max_time_difference

        # query the pollutant sensors
        sql = 'SELECT '
        pollution_sensor_real_cols = []
        pollution_sensor_as_cols = []
        first = True
        for (as_col, real_col) in list(self._get_polution_sensor_columns().items()):
            pollution_sensor_real_cols.append(real_col)
            pollution_sensor_as_cols.append(as_col)
            if not first:
                sql += ', '
            sql += real_col + ' AS ' + as_col
            first = False
        sql += ' FROM %s WHERE %s >= ? AND %s <= ? ORDER BY %s ASC' % (self.sensor_dbm.table_name,
            self.sensor_epoch_seconds_column, self.sensor_epoch_seconds_column,
            self.sensor_epoch_seconds_column)
        pollutant_observations = self.sensor_dbm.genSql(sql, (start_time, end_time))

        # query the weather sensors
        weather_observations = iter([])
        weather_cols = self._get_weather_sensor_columns()
        weather_observations_real_cols = []
        weather_observations_as_cols = []
        if len(weather_cols) == 4:
            # the sensor has the proper confiruration, so use it
            sql = 'SELECT '
            first = True
            for (as_col, real_col) in list(weather_cols.items()):
                weather_observations_real_cols.append(real_col)
                weather_observations_as_cols.append(as_col)
                if not first:
                    sql += ', '
                sql += real_col + ' AS ' + as_col
                first = False
            sql += ' FROM %s WHERE %s >= ? AND %s <= ? ORDER BY %s ASC' % (
                self.sensor_dbm.table_name,
                self.sensor_epoch_seconds_column,
                self.sensor_epoch_seconds_column,
                self.sensor_epoch_seconds_column)
            weather_observations = self.sensor_dbm.genSql(sql, (start_time, end_time))
        else:
            # We can't get the weather data from the air sensor, so use the main sensor instead
            # See https://github.com/weewx/weewx/wiki/Barometer,-pressure,-and-altimeter
            weather_observations_real_cols = [ 'dateTime', 'outTemp', 'barometer', 'usUnits' ]
            weather_observations_as_cols = [ 'dateTime', 'outTemp', 'pressure', 'weather_usUnits' ]
            sql = 'SELECT '
            first = True
            for i in range(len(weather_observations_real_cols)):
                real_col = weather_observations_real_cols[i]
                as_col = weather_observations_as_cols[i]
                if not first:
                    sql += ', '
                sql += real_col + ' AS ' + as_col
                first = False
            sql += ' FROM archive WHERE dateTime >= ? AND dateTime <= ? ORDER BY dateTime ASC'
            weather_observations = self.weather_dbm.genSql(sql, (start_time, end_time))

        # we need to be able to map back to underlying column for unit conversion
        as_column_to_real_column = {}
        for i in range(len(pollution_sensor_as_cols)):
            as_column_to_real_column[pollution_sensor_as_cols[i]] = pollution_sensor_real_cols[i]
        for i in range(len(weather_observations_as_cols)):
            as_column_to_real_column[weather_observations_as_cols[i]] = weather_observations_real_cols[i]

        # join the weather and pollutant tables. We do the join in code, because
        # the data could have come through two different tables.
        joined = self._join_sensor_results(
            pollutant_observations, pollution_sensor_as_cols,
            weather_observations, weather_observations_as_cols,
            max_time_difference)

        if len(joined) == 0:
            return

        # convert sensor units to aqi required units, possibly using the weather columns
        for i in range(len(joined)):
            row = joined[i]
            # convert temperature to kelvin
            outTemp_unit = get_unit_from_column(as_column_to_real_column['outTemp'], row['weather_usUnits'])
            temp_kelvin = None
            if outTemp_unit == 'degree_C':
                temp_kelvin = weewx.units.CtoK(row['outTemp'])
            else:
                temp_kelvin = weewx.units.CtoK(weewx.units.FtoC(row['outTemp']))

            # convert pressure to pascals
            pressure_unit = get_unit_from_column(as_column_to_real_column['pressure'], row['weather_usUnits'])
            press_kilopascals = row['pressure']
            if pressure_unit != 'hPa':
                press_kilopascals = weewx.units.conversionDict[pressure_unit]['hPa'](press_kilopascals)
            press_kilopascals /= 10

            for (pollutant, required_unit) in list(self.aqi_standard.get_pollutants().items()):
                if pollutant in row:
                    # convert the observed pollution units to what's required by the standard
                    try:
                        obs_unit = get_unit_from_column(as_column_to_real_column[pollutant], row['usUnits'])
                    except KeyError:
                        syslog.syslog(syslog.LOG_WARNING, "AqiService: AQI calculation could not find unit for column %s, assuming %s" % (as_column_to_real_column[pollutant], required_unit))
                        obs_unit = required_unit
                    joined[i][pollutant] = units.convert_pollutant_units(pollutant, row[pollutant], obs_unit, required_unit, temp_kelvin, press_kilopascals)

        # calculate the AQIs
        record = {
            'dateTime': event.record['dateTime'],
            'usUnits': weewx.US,
            'interval': event.record['interval'],
            'aqi_standard': self.aqi_standard.guid,
        }
        all_pollutants_available = True
        for (pollutant, required_unit) in list(self.aqi_standard.get_pollutants().items()):
            if pollutant in joined[0]:
                try:
                    (record['aqi_' + pollutant], record['aqi_' + pollutant + '_category']) = \
                        self.aqi_standard.calculate_aqi(pollutant, required_unit, joined)
                except (ValueError) as e:
                    syslog.syslog(syslog.LOG_ERR, "AqiService: %s AQI calculation for %s on %s failed: %s" % (type(e).__name__, pollutant, event.record['dateTime'], str(e)))
                except NotImplementedError as e:
                    # Canada's AQHI does not define indcies for individual pollutants
                    pass
            else:
                all_pollutants_available = False
        if all_pollutants_available:
            try:
                (record['aqi_composite'], record['aqi_composite_category']) = \
                    self.aqi_standard.calculate_composite_aqi(self.aqi_standard.get_pollutants(), joined)
            except (ValueError, TypeError) as e:
                syslog.syslog(syslog.LOG_ERR, "AqiService: %s AQI calculation for composite on %s failed: %s" % (type(e).__name__, event.record['dateTime'], str(e)))

        if len(record) > 4:
            self.aqi_dbm.addRecord(record)
        else:
            syslog.syslog(syslog.LOG_ERR, "AqiService: not storing record for dateTime %d" % (now))


class AqiSearchList(weewx.cheetahgenerator.SearchList):
    '''Class that implements the '$aqi' tag in cheetah templates'''
    def __init__(self, generator):
        weewx.cheetahgenerator.SearchList.__init__(self, generator)
        config_dict = generator.config_dict

        # configure the aqi standard
        standard_config_dict = config_dict['AqiService']['standard']
        fq_standard = standard_config_dict['standard']
        standard_path = '.'.join(fq_standard.split('.')[:-1])
        standard_name = fq_standard.split('.')[-1]
        __import__(standard_path)
        standard_class = getattr(sys.modules[standard_path], standard_name)
        self.aqi_standard = standard_class(int(config_dict['StdArchive']['archive_interval']))

        self.search_list_extension = {
            'aqi': lambda x: self.aqi_standard.interpret_aqi_index(x.raw)
        }

    def get_extension_list(self, timespan, db_lookup):
        return [self.search_list_extension]
