import unittest

from bin.user.aqi.calculators import *
from bin.user.aqi.units import *

def num_decimals(x):
    return len(str(x)) - 2

class TestUnits(unittest.TestCase):
    def test_ppb_ugm3_conversions(self):
        test_cases = [
            {
                'pollutant': SO2,
                'ppb': 1,
                'ugm3': 2.858,
                'temp_in_k': IDEAL_GAS_TEMP_IN_KELVIN,
                'pres_in_kpa': IDEAL_GAS_PRESSURE_IN_KILOPASCALS
            },
            {
                'pollutant': NO2,
                'ppb': 1,
                'ugm3': 2.053,
                'temp_in_k': IDEAL_GAS_TEMP_IN_KELVIN,
                'pres_in_kpa': IDEAL_GAS_PRESSURE_IN_KILOPASCALS
            },
            {
                'pollutant': O3,
                'ppb': 1,
                'ugm3': 2.141,
                'temp_in_k': IDEAL_GAS_TEMP_IN_KELVIN,
                'pres_in_kpa': IDEAL_GAS_PRESSURE_IN_KILOPASCALS
            },

            {
                'pollutant': SO2,
                'ppb': 1,
                'ugm3': 2.62,
                'temp_in_k': IDEAL_GAS_TEMP_IN_KELVIN + 25,
                'pres_in_kpa': IDEAL_GAS_PRESSURE_IN_KILOPASCALS
            },
            {
                'pollutant': NO2,
                'ppb': 1,
                'ugm3': 1.88,
                'temp_in_k': IDEAL_GAS_TEMP_IN_KELVIN + 25,
                'pres_in_kpa': IDEAL_GAS_PRESSURE_IN_KILOPASCALS
            },
            {
                'pollutant': O3,
                'ppb': 1,
                'ugm3': 2.00,
                'temp_in_k': IDEAL_GAS_TEMP_IN_KELVIN + 25,
                'pres_in_kpa': IDEAL_GAS_PRESSURE_IN_KILOPASCALS
            },
            {
                'pollutant': CO,
                'ppb': 1,
                'ugm3': 1.145,
                'temp_in_k': IDEAL_GAS_TEMP_IN_KELVIN + 25,
                'pres_in_kpa': IDEAL_GAS_PRESSURE_IN_KILOPASCALS
            }
        ]
        for tc in test_cases:
            actual = ppb_to_microgram_per_meter_cubed(tc['pollutant'], tc['ppb'], tc['temp_in_k'], tc['pres_in_kpa'])
            self.assertAlmostEqual(actual, tc['ugm3'], num_decimals(tc['ugm3']))

            actual = microgram_per_meter_cubed_to_ppb(tc['pollutant'], tc['ugm3'], tc['temp_in_k'], tc['pres_in_kpa'])
            self.assertAlmostEqual(actual, tc['ppb'], num_decimals(tc['ugm3']))

            actual = convert_pollutant_units(tc['pollutant'], tc['ppb'], 'part_per_billion', 'microgram_per_meter_cubed', tc['temp_in_k'], tc['pres_in_kpa'])
            self.assertAlmostEqual(actual, tc['ugm3'], num_decimals(tc['ugm3']))

            actual = convert_pollutant_units(tc['pollutant'], tc['ppb'] * 1000, 'part_per_million', 'microgram_per_meter_cubed', tc['temp_in_k'], tc['pres_in_kpa'])
            self.assertAlmostEqual(actual, tc['ugm3'], num_decimals(tc['ugm3']))

            actual = convert_pollutant_units(tc['pollutant'], tc['ppb'] * 1000, 'part_per_million', 'milligram_per_meter_cubed', tc['temp_in_k'], tc['pres_in_kpa'])
            self.assertAlmostEqual(actual, tc['ugm3'] / 1000.0, num_decimals(tc['ugm3']))
