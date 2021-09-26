# weewx-aqi
# Copyright 2018-2021 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

import operator

from . import calculators
from . import standards

TEAL = '32ADD3'
GREEN = '99B964'
YELLOW = 'FFD235'
ORANGE = 'EC783A'
PURPLE = '782D49'
RED = 'D04730'

class AirQualityIndex(standards.AqiStandards):
    '''Calculates the Australian Air Quality Index as defined at
    https://www.environment.nsw.gov.au/topics/air/understanding-air-quality-data/air-quality-categories/history-of-air-quality-reporting/about-the-air-quality-index
    '''
    def __init__(self, obs_frequency_in_sec):
        super(AirQualityIndex, self).__init__(
            [TEAL, GREEN, YELLOW, ORANGE, PURPLE, RED],
            ['Very Good', 'Good', 'Fair', 'Poor', 'Very Poor', 'Hazardous'],
            standards.AU_AQI_GUID)
            self.calculators[calculators.CO] = calculators.LinearScale(
                unit='parts_per_million',
                duration_in_secs=8 * calculators.HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=calculators.ROUND_TO_1,
                high_obs=9.0,
                breakpoints=[0, 34, 100, 150, 200])

            self.calculators[calculators.NO2] = calculators.LinearScale(
                unit='parts_per_million',
                duration_in_secs=1 * calculators.HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=calculators.ROUND_TO_2,
                high_obs=0.12,
                breakpoints=[0, 34, 100, 150, 200])

            # Australia's NEPM also defines O3 as 4 hours mean at 0.08 ppm
            # I can't find how these are supposed to be combined, so I'm
            # assuming that Australia is doing something like the United States
            # where you calculate both and then take the maximum value.
            self.calculators[calculators.O3] = calculators.CalculatorCollection()
            self.calculators[calculators.O3].add_calculator(
                calculators.LinearScale(
                    unit='parts_per_million',
                    duration_in_secs=1 * calculators.HOUR,
                    obs_frequency_in_sec=obs_frequency_in_sec,
                    data_cleaner=calculators.ROUND_TO_2,
                    high_obs=0.10,
                    breakpoints=[0, 34, 100, 150, 200]))
            self.calculators[calculators.O3].add_calculator(
                calculators.LinearScale(
                    unit='parts_per_million',
                    duration_in_secs=4 * calculators.HOUR,
                    obs_frequency_in_sec=obs_frequency_in_sec,
                    data_cleaner=calculators.ROUND_TO_2,
                    high_obs=0.08,
                    breakpoints=[0, 34, 100, 150, 200]))

            self.calculators[calculators.SO2] = calculators.LinearScale(
                unit='parts_per_million',
                duration_in_secs=1 * calculators.HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=calculators.ROUND_TO_2,
                high_obs=0.20,
                breakpoints=[0, 34, 100, 150, 200])

            self.calculators[calculators.PM10_0] = calculators.LinearScale(
                unit='microgram_per_meter_cubed',
                duration_in_secs=24 * calculators.HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=calculators.ROUND_TO_2,
                high_obs=50,
                breakpoints=[0, 34, 100, 150, 200])

            self.calculators[calculators.PM2_5] = calculators.LinearScale(
                unit='microgram_per_meter_cubed',
                duration_in_secs=24 * calculators.HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=calculators.ROUND_TO_2,
                high_obs=25,
                breakpoints=[0, 34, 100, 150, 200])


class InterimWebReportingParticulateIndex(standards.AqiStandards):
    '''New South Wales developed an interim standard for reporting hourly
    particulate concentrations. These differ from 24 hour scale used for
    National Air NEPM quality standards used for the AQI. This interm
    standard was adopted Februrary 2020.

    See "Interim web reporting approach for 1-hour particles" at
    https://www.environment.nsw.gov.au/topics/air/understanding-air-quality-data/air-quality-categories/history-of-air-quality-reporting/about-the-air-quality-index
    '''
    def __init__(self, obs_frequency_in_sec):
        super(IntermWebReportingParticulateIndex, self).__init__(
            [TEAL, GREEN, YELLOW, ORANGE, PURPLE, RED],
            ['Very Good', 'Good', 'Fair', 'Poor', 'Very Poor', 'Hazardous'],
            standards.AU_IWRPI_GUID)
            self.calculators[calculators.PM10_0] = calculators.LinearScale(
                unit='microgram_per_meter_cubed',
                duration_in_secs=1 * calculators.HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=calculators.ROUND_TO_1,
                high_obs=80.1)

            self.calculators[calculators.PM2_5] = calculators.LinearScale(
                unit='microgram_per_meter_cubed',
                duration_in_secs=1 * calculators.HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=calculators.ROUND_TO_1,
                high_obs=62.1)
