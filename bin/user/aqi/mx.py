# -*- coding: utf-8-*-

# weewx-aqi
# Copyright 2018-2021 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

import operator

from . import calculators
from . import standards

GREEN = '00e400'
YELLOW = 'ffff00'
ORANGE = 'ff7e00'
RED = 'ff0000'
PURPLE = '8f3f97'

class IndiceMetropolitanoCalidadAire(standards.AqiStandards):
    '''Calculates Mexico's Índice Metropolitano de la Calidad del Aire (IMECA)
    (Metropolitan Air Quality Index) as described in
    https://es.wikipedia.org/wiki/%C3%8Dndice_Metropolitano_de_la_Calidad_del_Aire#Categor%C3%ADas_del_%C3%8Dndice_Metropolitano_de_Calidad_del_Aire
    http://www.aire.cdmx.gob.mx/descargas/monitoreo/normatividad/NADF-009-AIRE-2006.pdf
    '''
    def __init__(self, obs_frequency_in_sec):
        super(IndiceMetropolitanoCalidadAire, self).__init__(
            [GREEN, YELLOW, ORANGE, RED, PURPLE],
            ['Good', 'Regular', 'Bad', 'Very Bad', 'Extremely Bad'],
            standards.MX_IMCA_GUID)
        self.obs_frequency_in_sec = obs_frequency_in_sec

        self.calculators[calculators.O3] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_3,
            unit='microgram_per_meter_cubed',
            duration_in_secs=1 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  1,  50, 0.000, 0.055, lambda bp, obs: obs * 100.0 / 0.11) \
            .add_breakpoint( 51, 100, 0.056, 0.110, lambda bp, obs: obs * 100.0 / 0.11) \
            .add_breakpoint(101, 150, 0.111, 0.165, lambda bp, obs: obs * 100.0 / 0.11) \
            .add_breakpoint(151, 200, 0.166, 0.220, lambda bp, obs: obs * 100.0 / 0.11) \
            .add_breakpoint(201, 999, 0.221, 9.999, lambda bp, obs: obs * 100.0 / 0.11)    # no upper bound

        self.calculators[calculators.NO2] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_3,
            unit='microgram_per_meter_cubed',
            duration_in_secs=1 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  1,  50, 0.000, 0.105, lambda bp, obs: obs * 100.0 / 0.21) \
            .add_breakpoint( 51, 100, 0.106, 0.210, lambda bp, obs: obs * 100.0 / 0.21) \
            .add_breakpoint(101, 150, 0.211, 0.315, lambda bp, obs: obs * 100.0 / 0.21) \
            .add_breakpoint(151, 200, 0.316, 0.420, lambda bp, obs: obs * 100.0 / 0.21) \
            .add_breakpoint(201, 999, 0.421, 9.999, lambda bp, obs: obs * 100.0 / 0.21)    # no upper bound

        self.calculators[calculators.SO2] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_3,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  1,  50, 0.000, 0.065, lambda bp, obs: obs * 100.0 / 0.13) \
            .add_breakpoint( 51, 100, 0.066, 0.130, lambda bp, obs: obs * 100.0 / 0.13) \
            .add_breakpoint(101, 150, 0.131, 0.195, lambda bp, obs: obs * 100.0 / 0.13) \
            .add_breakpoint(151, 200, 0.196, 0.260, lambda bp, obs: obs * 100.0 / 0.13) \
            .add_breakpoint(201, 999, 0.261, 9.999, lambda bp, obs: obs * 100.0 / 0.13)    # no upper bound

        self.calculators[calculators.CO] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_2,
            unit='microgram_per_meter_cubed',
            duration_in_secs=8 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  1,  50,  0.00,  5.50, lambda bp, obs: obs * 100.0 / 11.0) \
            .add_breakpoint( 51, 100,  5.51, 11.00, lambda bp, obs: obs * 100.0 / 11.0) \
            .add_breakpoint(101, 150, 11.01, 16.50, lambda bp, obs: obs * 100.0 / 11.0) \
            .add_breakpoint(151, 200, 16.51, 22.00, lambda bp, obs: obs * 100.0 / 11.0) \
            .add_breakpoint(201, 999, 22.01, 99.99, lambda bp, obs: obs * 100.0 / 11.0)    # no upper bound

        self.calculators[calculators.PM10_0] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_0,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  1,  50,   0,  60, lambda bp, obs: obs * 5.0 / 6.0) \
            .add_breakpoint( 51, 100,  61, 120, lambda bp, obs: obs * 5.0 / 6.0) \
            .add_breakpoint(101, 150, 121, 220, lambda bp, obs: 40.0 + obs * 0.5) \
            .add_breakpoint(151, 200, 221, 320, lambda bp, obs: 40.0 + obs * 0.5) \
            .add_breakpoint(201, 999, 321, 999, lambda bp, obs: obs * 5.0 / 8.0)    # no upper bound

        self.calculators[calculators.PM2_5] = calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_1,
            unit='microgram_per_meter_cubed',
            duration_in_secs=24 * calculators.HOUR,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint(  1,  50,   0.0,  15.4, lambda bp, obs: obs * 50.0 / 15.4) \
            .add_breakpoint( 51, 100,  15.5,  40.4, lambda bp, obs: 20.5 + obs * 49.0 / 24.9) \
            .add_breakpoint(101, 150,  40.5,  65.4, lambda bp, obs: 21.3 + obs * 49.0 / 24.9) \
            .add_breakpoint(151, 200,  65.5, 150.4, lambda bp, obs: 113.20 + obs * 49.0 / 84.9) \
            .add_breakpoint(201, 999, 150.5, 999.9, lambda bp, obs: obs * 201.0 / 150.5)    # no upper bound
