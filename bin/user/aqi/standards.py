# weewx-aqi
# Copyright 2018-2020 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

from abc import ABCMeta, abstractmethod

from . import calculators

CA_AQHI_GUID = 1
IN_NAQI_GUID = 2
MX_IMCA_GUID = 3
UK_DAQI_GUID = 4
US_AQI_GUID = 5
US_NOWCAST_GUID = 6
EU_AQI_GUID = 7

class AqiStandards(metaclass=ABCMeta):
    def __init__(self, colors, categories, guid):
        '''Creates an AqiStandard with the specified color and categorical scales.
        self.calculators is initalized to an empty dictionary. It is up to
        implementations to populate this dictionary as a map of pollutants to
        aqi.AqiCalculator calulators.'''
        self.colors = colors
        self.categories = categories
        self.guid = guid
        self.calculators = {}

    def max_duration(self):
        '''Returns the maximum duration window for the calculator.'''
        max = -1
        for c in list(self.calculators.values()):
            if c.max_duration() > max:
                max = c.max_duration()
        return max

    def get_pollutants(self):
        '''Returns a map of the pollutants monitored by the standard to their
        required units.'''
        d = {}
        for (pollutant, calculator) in list(self.calculators.items()):
            d[pollutant] = calculator.unit
        return d

    def calculate_aqi(self, pollutant, observation_unit, observations):
        '''Calculates the AQI for the specified pollutant. If the AQI is undefined
        for the pollutant, raises KeyError. If the calculated AQI value is undefined,
        raises ValueError. If the data is recorded in the wrong units, raises ValueError
        Observations are recorded as an array of maps containing keys `dateTime`
        (containing epoch seconds for the observation) and the key specified by
        `pollutant` with a value recorded in units of `observation_unit`.
        Returns a pair containing the AQI and the index to the AQI category.'''
        return self.calculators[pollutant].calculate(pollutant, observation_unit, observations)

    def calculate_composite_aqi(self, pollutants_and_units, observations):
        '''Calculates the AQI over the list of pollutants. Throws the appropriate
        error if the any of the AQIs can not calculated.'''
        # Per https://www3.epa.gov/airnow/aqi-technical-assistance-document-may2016.pdf ,
        # multiple AQIs (i.e. AQIs from multiple pollutants) can be combined by
        # simply taking the maximum value of theaqis.
        #
        # (Yes, the is a US-centric standard, but it also the most common method,
        # of combining AQIs.)
        max_aqi = -1
        max_aqi_index = -1
        for pollutant in pollutants_and_units:
            observation_unit = pollutants_and_units[pollutant]
            (aqi, aqi_index) = self.calculate_aqi(pollutant, observation_unit, observations)
            if aqi > max_aqi:
                max_aqi = aqi
                max_aqi_index = aqi_index
        return (max_aqi, aqi_index)

    def interpret_aqi_index(self, aqi_index):
        '''Returns the color and category name associated with the pollutant
        with the aqi_index (not aqi value).'''
        if aqi_index is None:
            return {
                'color': 'None',
                'category': 'None'
            }
        return {
            'color': self.colors[int(aqi_index)],
            'category': self.categories[int(aqi_index)]
        }
