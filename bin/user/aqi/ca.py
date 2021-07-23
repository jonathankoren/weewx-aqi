# weewx-aqi
# Copyright 2018-2021 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

from . import calculators
import math
from . import standards

# Colors defiend by https://www3.epa.gov/airnow/aqi-technical-assistance-document-may2016.pdf
COLOR_1 = '00CCFF'
COLOR_2 = '0099CC'
COLOR_3 = '006699'
COLOR_4 = 'FFFF00'
COLOR_5 = 'FFFF00'
COLOR_6 = 'FF9933'
COLOR_7 = 'FF6666'
COLOR_8 = 'FF0000'
COLOR_9 = 'CC0000'
COLOR_10 = '990000'
COLOR_PLUS = '660000'

class AirQualityHealthIndex(standards.AqiStandards):
    '''Calculates the Canadian Air Quality Health Index (AQHI) according to the
    https://en.wikipedia.org/wiki/Air_Quality_Health_Index_(Canada)'''
    def __init__(self, obs_frequency_in_sec):
        super(AirQualityHealthIndex, self).__init__(
            [COLOR_1, COLOR_2, COLOR_3, COLOR_4, COLOR_5, COLOR_6, COLOR_7, COLOR_8, COLOR_9, COLOR_10, COLOR_PLUS],
            ['Low', 'Low', 'Low', 'Moderate', 'Moderate', 'Moderate', 'High', 'High', 'High', 'High', 'Very High'],
            standards.CA_AQHI_GUID)
        self.calculators[calculators.O3] = calculators.ArithmeticMean(
            unit='parts_per_billion',
            duration_in_secs=3 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec,
            data_cleaner=calculators.TRUNCATE_TO_0,
            required_observation_ratio=0.6667,
        )
        self.calculators[calculators.NO2] = calculators.ArithmeticMean(
            unit='parts_per_billion',
            duration_in_secs=3 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec,
            data_cleaner=calculators.TRUNCATE_TO_0,
            required_observation_ratio=0.6667,
        )
        self.calculators[calculators.PM2_5] = calculators.ArithmeticMean(
            unit='microgram_per_meter_cubed',
            duration_in_secs=3 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec,
            data_cleaner=calculators.TRUNCATE_TO_1,
            required_observation_ratio=0.6667,
        )

    def calculate_aqi(self, pollutant, observation_unit, observations):
        raise NotImplementedError('AQHI is defined as composite index only')

    def calculate_composite_aqi(self, pollutants_and_units, observations):
        '''Calcuations are based on the 3 hour average of O3 (ppb), NO2 (ppb), and PM2.5 (ug/m^3).
        Throws ValueError, if readings from all three pollutants are not available.'''
        observations = observations[:get_last_valid_index(self, observations, 3 * calculators.HOUR) + 1]
        validate_number_of_observations(observations, self.duration_in_secs, obs_frequency_in_sec, 0.67)

        # calculate features
        try:
            o3 = self.calculators[calculators.O3].calculate(calculators.O3, pollutants_and_units[calculators.O3], observations)[0]
            no2 = self.calculators[calculators.NO2].calculate(calculators.NO2, pollutants_and_units[calculators.NO2], observations)[0]
            pm2_5 = self.calculators[calculators.PM2_5].calculate(calculators.PM2_5, pollutants_and_units[calculators.PM2_5], observations)[0]
        except KeyError:
            raise ValueError("Can't calculate AQHI. Requries O3, NO2, and PM2_5 readings")

        # now calcualte the AQHI
        aqhi = round((1000 / 10.4) * ((math.exp(0.000537 * o3) - 1) + (math.exp(0.000871 * no2) - 1) + (math.exp(0.000487 * pm2_5) - 1)))
        if aqhi == 0:
            aqhi = 1
        index = aqhi - 1
        if index >= 10:
            index = 10
        return (aqhi, index)
