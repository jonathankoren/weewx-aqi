# weewx-aqi
# Copyright 2018-2021 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

import operator

from . import calculators
from . import standards

GREEN = '00B04E'
LIGHT_GREEN = '93C953'
PINK = 'E5B8B6'
ORANGE = 'FDBF0F'
RED = 'EC1F24'
DARK_RED = 'BE1F26'

class NationalAirQualityIndex(standards.AqiStandards):
    '''Calculates India's National Air Quality Index (AQI) as defined by the
    Indian Central Pollution Control Board in
    http://www.indiaenvironmentportal.org.in/files/file/Air%20Quality%20Index.pdf
    Upperbounds are unfortunately not defined in that document, but some
    can be found through experiment in
    https://web.archive.org/web/20170713083922if_/http://cpcb.nic.in/AQI%20-Calculator.xls

    Please note AQI values [400, 500] may be incorrect (in particular for O3 and Pb),
    due to lack of specification in the standards document.'''
    def __init__(self, obs_frequency_in_sec):
        super(NationalAirQualityIndex, self).__init__(
            [GREEN, LIGHT_GREEN, PINK, ORANGE, RED, DARK_RED],
            ['Good', 'Satisfactory', 'Moderately Polluted', 'Poor', 'Very Poor', 'Severe'],
            standards.IN_NAQI_GUID)

        # These breakpooints are taken from page 26 of the PDF linked above.
        # Upper bounds for mapping to a 500 AQI were found vas found experimentally
        # with the Excel spreadsheet.
        self.calculators[calculators.PM10_0] = calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_0,
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50,   0,  50) \
            .add_breakpoint( 51, 100,  51, 100) \
            .add_breakpoint(101, 200, 101, 250) \
            .add_breakpoint(201, 300, 251, 350) \
            .add_breakpoint(301, 400, 351, 430) \
            .add_breakpoint(401, 500, 431, 510)      # Excel calculator range

        self.calculators[calculators.PM2_5] = calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_0,
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50,   0,  30) \
            .add_breakpoint( 51, 100,  31,  60) \
            .add_breakpoint(101, 200,  61,  90) \
            .add_breakpoint(201, 300,  91, 120) \
            .add_breakpoint(301, 400, 121, 250) \
            .add_breakpoint(401, 500, 251, 380)      # Excel calculator range

        self.calculators[calculators.NO2] = calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_0,
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50,   0,  40) \
            .add_breakpoint( 51, 100,  41,  80) \
            .add_breakpoint(101, 200,  81, 180) \
            .add_breakpoint(201, 300, 181, 280) \
            .add_breakpoint(301, 400, 281, 400) \
            .add_breakpoint(401, 500, 401, 520)      # Excel calculator range

        self.calculators[calculators.O3] = calculators.CalculatorCollection()
        self.calculators[calculators.O3].add_calculator(calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_0,
            mean_cleaner=calculators.ROUND_TO_0,
            mean_calculator=max,            # not average, it's a maximum
            unit='microgram_per_meter_cubed',
            duration_in_secs=8 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50,   0,  50) \
            .add_breakpoint( 51, 100,  51, 100) \
            .add_breakpoint(101, 200, 101, 168) \
            .add_breakpoint(201, 300, 169, 208)
        self.calculators[calculators.O3].add_calculator(calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_0,
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=1 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec,
            bp_index_offset=4) \
            .add_breakpoint(301, 400, 209,  748) \     # lower bound not defined(!) Pure speculation.
            .add_breakpoint(401, 500, 749, 1288)       # upper bound not defined(!) Pure speculation.

        self.calculators[calculators.CO] = calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_1,
            mean_cleaner=calculators.ROUND_TO_1,
            mean_calculator=max,            # not average, it's a maximum
            unit='milligram_per_meter_cubed',
            duration_in_secs=8 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50,  0.0,  1.0) \
            .add_breakpoint( 51, 100,  1.1,  2.0) \
            .add_breakpoint(101, 200,  2.1, 10.0) \
            .add_breakpoint(201, 300, 10.1, 17.0) \
            .add_breakpoint(301, 400, 17.1, 34.0) \
            .add_breakpoint(401, 500, 34.1, 51.0)      # Excel calculator range

        self.calculators[calculators.SO2] = calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_0,
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50,    0,   40) \
            .add_breakpoint( 51, 100,   41,   80) \
            .add_breakpoint(101, 200,   81,  380) \
            .add_breakpoint(201, 300,  381,  800) \
            .add_breakpoint(301, 400,  801, 1600) \
            .add_breakpoint(401, 500, 1601, 2400)      # Excel calculator range is [2396, 2403]

        self.calculators[calculators.NH3] = calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_0,
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50,    0,  200) \
            .add_breakpoint( 51, 100,  201,  400) \
            .add_breakpoint(101, 200,  401,  800) \
            .add_breakpoint(201, 300,  801, 1200) \
            .add_breakpoint(301, 400, 1201, 1800) \
            .add_breakpoint(401, 500, 1801, 2400)      # Excel calculator range

        self.calculators[calculators.PB] = calculators.BreakpointTable(
            data_cleaner=calculators.ROUND_TO_1,
            mean_cleaner=calculators.ROUND_TO_1,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  0,  50, 0.0, 0.5) \
            .add_breakpoint( 51, 100, 0.6, 1.0) \
            .add_breakpoint(101, 200, 1.1, 2.0) \
            .add_breakpoint(201, 300, 2.1, 3.0) \
            .add_breakpoint(301, 400, 3.1, 3.5) \
            .add_breakpoint(401, 500, 3.6, 4.0)      # upper bound not defined(!) Pure speculation.
