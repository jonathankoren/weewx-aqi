# weewx-aqi
# Copyright 2018-2021 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

import operator

from . import calculators
from . import standards

# colors taken from https://en.wikipedia.org/wiki/Air_quality_index#United_Kingdom
COLOR_1  = 'CCFFCC'
COLOR_2  = '66FF66'
COLOR_3  = '00FF00'
COLOR_4  = '99FF00'
COLOR_5  = 'FFFF00'
COLOR_6  = 'FFCC00'
COLOR_7  = 'FF6600'
COLOR_8  = 'FF3300'
COLOR_9  = 'FF0000'
COLOR_10 = 'FF0066'

class DailyAirQualityIndex(standards.AqiStandards):
    '''Calucates the United Kingdom's Daily Air Quality Index (DAQI), as described in
    https://uk-air.defra.gov.uk/assets/documents/reports/cat14/1304251155_Update_on_Implementation_of_the_DAQI_April_2013_Final.pdf'''
    def __init__(self, obs_frequency_in_sec):
        super(DailyAirQualityIndex, self).__init__(
            [COLOR_1, COLOR_2, COLOR_3, COLOR_4, COLOR_5, COLOR_6, COLOR_7, COLOR_8, COLOR_9, COLOR_10],
            ['Low', 'Low', 'Low', 'Moderate', 'Moderate', 'Moderate', 'High', 'High', 'High', 'Very High'],
            standards.UK_DAQI_GUID)

        self.calculators[calculators.O3] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=8 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,   0,  33) \
            .add_breakpoint( 2,  2,  34,  66) \
            .add_breakpoint( 3,  3,  67, 100) \
            .add_breakpoint( 4,  4, 101, 120) \
            .add_breakpoint( 5,  5, 121, 140) \
            .add_breakpoint( 6,  6, 141, 160) \
            .add_breakpoint( 7,  7, 161, 187) \
            .add_breakpoint( 8,  8, 188, 213) \
            .add_breakpoint( 9,  9, 214, 240) \
            .add_breakpoint(10, 10, 241, 9999)      # no upper bound

        self.calculators[calculators.NO2] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=1 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,   0,  67) \
            .add_breakpoint( 2,  2,  68, 134) \
            .add_breakpoint( 3,  3, 135, 200) \
            .add_breakpoint( 4,  4, 201, 267) \
            .add_breakpoint( 5,  5, 268, 334) \
            .add_breakpoint( 6,  6, 335, 400) \
            .add_breakpoint( 7,  7, 401, 467) \
            .add_breakpoint( 8,  8, 468, 534) \
            .add_breakpoint( 9,  9, 535, 600) \
            .add_breakpoint(10, 10, 601, 9999)      # no upper bound

        self.calculators[calculators.SO2] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=15 * calculators.MINUTE,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,    0,   88) \
            .add_breakpoint( 2,  2,   89,  177) \
            .add_breakpoint( 3,  3,  178,  266) \
            .add_breakpoint( 4,  4,  267,  354) \
            .add_breakpoint( 5,  5,  355,  443) \
            .add_breakpoint( 6,  6,  444,  532) \
            .add_breakpoint( 7,  7,  533,  710) \
            .add_breakpoint( 8,  8,  711,  887) \
            .add_breakpoint( 9,  9,  888, 1064) \
            .add_breakpoint(10, 10, 1065, 9999)    # no upper bound

        self.calculators[calculators.PM2_5] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,  0, 11) \
            .add_breakpoint( 2,  2, 12, 23) \
            .add_breakpoint( 3,  3, 24, 35) \
            .add_breakpoint( 4,  4, 36, 41) \
            .add_breakpoint( 5,  5, 42, 47) \
            .add_breakpoint( 6,  6, 48, 53) \
            .add_breakpoint( 7,  7, 54, 58) \
            .add_breakpoint( 8,  8, 59, 64) \
            .add_breakpoint( 9,  9, 65, 70) \
            .add_breakpoint(10, 10, 71, 9999)    # no upper bound

        self.calculators[calculators.PM10_0] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,   0,  16) \
            .add_breakpoint( 2,  2,  17,  33) \
            .add_breakpoint( 3,  3,  34,  50) \
            .add_breakpoint( 4,  4,  51,  58) \
            .add_breakpoint( 5,  5,  59,  66) \
            .add_breakpoint( 6,  6,  67,  75) \
            .add_breakpoint( 7,  7,  76,  83) \
            .add_breakpoint( 8,  8,  84,  91) \
            .add_breakpoint( 9,  9,  92, 100) \
            .add_breakpoint(10, 10, 101, 9999)  # no upper bound
