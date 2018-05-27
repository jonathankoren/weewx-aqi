# weewx-aqi
# Copyright 2018 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

from abc import ABCMeta, abstractmethod
import operator

# number of seconds
MINUTE = 60
HOUR = 3600
DAY = 86400

# data cleaning functions
IDENTITY = lambda x: x
ROUND_TO_0 = lambda x: round(x)
ROUND_TO_1 = lambda x: round(x, 1)
ROUND_TO_2 = lambda x: round(x, 2)
ROUND_TO_3 = lambda x: round(x, 3)
TRUNCATE_TO_0 = lambda x: int(x)
TRUNCATE_TO_1 = lambda x: int(x * 10) / 10.0

# polution constants
PM2_5 = 'pm2_5'
PM10_0 = 'pm10_0'
CO = 'co'
NO2 = 'no2'
SO2 = 'so2'
O3 = 'o3'
NH3 = 'nh3'
PB = 'pb'

def get_last_valid_index(observations, duration_in_secs):
    '''Returns index into observations of the observation that is the
    closest, but not earlier than, earliest_valid_timestamp.'''
    earliest_valid_timestamp = observations[0][0] - duration_in_secs
    best_delta = None
    best_index = None
    start = 0
    end = len(observations)
    while start < end:
        mid = int((end - start) / 2) + start
        delta = observations[mid][0] - earliest_valid_timestamp;
        if delta < 0:
            # observation is too early
            end = mid
        else:
            # observation might be valid
            if best_delta is None or best_delta > delta:
                best_delta = delta
                best_index = mid
                start = mid + 1
            else:
                # worst delta, go to the front
                end = mid
    if best_index is None:
        raise ValueError('all observations are outside the valid range')
    return best_index

def validate_number_of_observations(observations, duration_in_secs, obs_frequency_in_sec, required_observation_ratio):
    '''Checks that there are enough observations to calculate a metric. If not
    enough observations are present, throws ValueError.'''
    num_required = (duration_in_secs / obs_frequency_in_sec) * required_observation_ratio
    if len(observations) < num_required:
        raise ValueError('Not enough observations wanted %d, but got %d' % (num_required, len(observations)))

def linear_interoplate(breakpoint, obs_mean):
    numerator = (obs_mean - breakpoint['low_obs']) * (breakpoint['high_aqi'] - breakpoint['low_aqi'])
    denominator = breakpoint['high_obs'] - breakpoint['low_obs']
    return int(round((numerator / denominator) + breakpoint['low_aqi']))

def arithmetic_mean(observations):
    '''Calculates the arithmetic mean from a set of observations.
    `observations` is reverse chronologically sorted array timestamped
    readings. Each reading is a pair, with epoch seconds first, followed by
    the measurment.'''
    obs_mean = 0
    for obs in observations:
        obs_mean = obs_mean + obs[1]
    return obs_mean / float(len(observations))

class AqiCalculator:
    __metaclass__ = ABCMeta
    def __init__(self, **kwargs):
        '''Creates a new AqiCalculator. Takes the following keyword arguments:
            data_cleaner
                function to be applied to each observation prior to calculation
                DEFAULT: IDENTITY

            mean_cleaner
                function to be applied after the mean calculation
                DEFAULT: IDENTITY

            unit (REQUIRED)
                units the observations are in

            duration_in_secs (REQUIRED)
                number of seconds of observations the AQI is calculated over

            obs_frequency_in_sec (REQUIRED)
                expected number of seconds between observations

            required_observation_ratio
                ratio of observations made to total possible observations
                that must be present in order to calculate the AQI
                DEFAULT: 0.75
        '''
        # set defaults
        params = {
            'data_cleaner': IDENTITY,
            'mean_cleaner': IDENTITY,
            # unit (REQUIRED, so it's missing here)
            # duration_in_secs (REQUIRED)
            # obs_frequency_in_sec (REQUIRED)
            'required_observation_ratio': 0.75,
        }
        params.update(kwargs)
        self.data_cleaner = params['data_cleaner']
        self.mean_cleaner = params['mean_cleaner']
        self.unit = params['unit']
        self.obs_frequency_in_sec = params['obs_frequency_in_sec']
        self.required_observation_ratio = params['required_observation_ratio']
        self.duration_in_secs = params['duration_in_secs']

    def max_duration(self):
        '''Returns the maximum duration window for the calculator.'''
        return self.duration_in_secs

    @abstractmethod
    def calculate(self, pollutant, observation_unit, observations):
        '''Returns the AQI index for the set of observations.
        Observations are recorded as an array of maps containing keys `dateTime`
        (containing epoch seconds for the observation) and the key specified by
        `pollutant` with a value recorded in units of `observation_unit`.
        Returns a pair containing the AQI and the index to the AQI category.

        NOTE: It is imperative that implementations verify the units of
        observations (performing conversions if appropriate), prior calculation.
        Raises ValueError if the observations are somehow invalid (e.g. wrong
        units, wrong time range, too many missing values, etc.).'''

class AqiTable(AqiCalculator):
    '''Calculates an air quality index (AQI) from a table. Each entry in the
    table contains a mapping of a rage of AQI values to a range of pollutant
    concentrations. The specific AQI value is determined by a linear
    interpolation of pollutant concentration to AQI value defined for the
    range.'''
    def __init__(self, **kwargs):
        '''Creates a new AqiTable'''
        # we don't need anything here, we're just implementing the interface.
        # BreakpointTables do all the work.
        super(AqiTable, self).__init__(unit=None, duration_in_secs=None, obs_frequency_in_sec=None)
        self.breakpoint_tables = []

    def add_breakpoint_table(self, breakpoint_table):
        '''Creates, and returns, a new BreakpointTable to the AqiTable that is
        valid for observations in the specified time range'''
        self.breakpoint_tables.append(breakpoint_table)
        self.unit = self.breakpoint_tables[0].unit
        return breakpoint_table

    def max_duration(self):
        max_dur = 0
        for t in self.breakpoint_tables:
            if t.max_duration() > max_dur:
                max_dur = t.max_duration()
        return max_dur

    def calculate(self, pollutant, observation_unit, observations):
        aqi_result = None
        for table in self.breakpoint_tables:
            try:
                res = table.calculate(pollutant, observation_unit, observations)
                if (aqi_result is None) or (res[0] > aqi_result[0]):
                    aqi_result = res
            except IndexError:
                pass
        if aqi_result != None:
            return aqi_result
        else:
            raise ValueError('AQI could not be calculated for the observations')

class BreakpointTable(AqiCalculator):
    '''This class is used to build the AqiTable.'''
    def __init__(self, **kwargs):
        '''Creates a new breakpoint table that is valid for observations in
        the specified time range. This table is initially empty.

        Additional kwargs:
            bp_index_offset
                First entry of this BreakpointTable corresponds to this AQI index
                DEFAULT: 0
            mean_calculator
                Function that returns the mean observation from a list of samples
                DEFAULT: arithmetic_mean
        '''
        super(BreakpointTable, self).__init__(**kwargs)
        if 'bp_index_offset' in kwargs:
            self.bp_index_offset = kwargs['bp_index_offset']
        else:
            self.bp_index_offset = 0
        if 'mean_calculator' not in kwargs:
            self.mean_calculator = arithmetic_mean
        else:
            self.mean_calculator = kwargs['mean_calculator']
        self.breakpoints = []

    def add_breakpoint(self, low_aqi, high_aqi, low_obs, high_obs, function=linear_interoplate):
        '''Adds an entry to the table, mapping a range of AQIs to a range of observations.'''
        self.breakpoints.append({
            'low_aqi':  low_aqi,
            'high_aqi': high_aqi,
            'low_obs':  low_obs,
            'high_obs': high_obs,
            'function': function,
        })
        self.breakpoints = sorted(self.breakpoints, key=operator.itemgetter('low_obs'))
        return self

    def calculate(self, pollutant, observation_unit, observations):
        '''Calculates the AQI for a particular breakpoint.'''
        # check the units
        if observation_unit != self.unit:
            raise ValueError('inappropriate units, expected %s, but got %s' % (self.unit, observation_unit))

        # clean the data
        observations = sorted(observations, key=operator.itemgetter('dateTime'), reverse=True)
        for i in range(len(observations)):
            observations[i] = (observations[i]['dateTime'], self.data_cleaner(observations[i][pollutant]))

        # validate observations
        last_valid_index = get_last_valid_index(observations, self.duration_in_secs)
        observations = observations[:last_valid_index + 1]
        validate_number_of_observations(observations,
            self.duration_in_secs,
            self.obs_frequency_in_sec,
            self.required_observation_ratio)

        # calculate the mean observation
        obs_mean = self.mean_cleaner(self.mean_calculator(observations))

        for bp_index in range(len(self.breakpoints)):
            breakpoint = self.breakpoints[bp_index]
            if breakpoint['low_obs'] <= obs_mean and obs_mean <= breakpoint['high_obs']:
                return (breakpoint['function'](breakpoint, obs_mean), bp_index + self.bp_index_offset)
        raise IndexError('AQI can not be calculated from this table')

class ArithmeticMean(AqiCalculator):
    '''Simply calculates the arithmetic mean of a set of observations.'''
    def calculate(self, pollutant, observation_unit, observations):
        # check the units
        if observation_unit != self.unit:
            raise ValueError('inappropriate units, expected %s, but got %s' % (self.unit, observation_unit))

        # clean the data
        observations = sorted(observations, key=operator.itemgetter('dateTime'), reverse=True)
        for i in range(len(observations)):
            observations[i] = (observations[i]['dateTime'], self.data_cleaner(observations[i][pollutant]))

        # validate observations
        last_valid_index = get_last_valid_index(observations, self.duration_in_secs)
        observations = observations[:last_valid_index + 1]
        validate_number_of_observations(observations,
            self.duration_in_secs,
            self.obs_frequency_in_sec,
            self.required_observation_ratio)

        # calculate the mean observation
        obs_sum = 0
        for obs in observations:
            obs_sum = obs_sum + obs[1]
        return self.mean_cleaner(obs_sum / float(len(observations)))
