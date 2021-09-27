import unittest

from bin.user.aqi.calculators import *

def make_observations(pollutant, obs_frequency_in_sec, observation_elapsed_time_in_secs):
    readings = [1,2,3,4,5,6,5,4,3,2,1,0]
    obs = [None] * int(observation_elapsed_time_in_secs / obs_frequency_in_sec)
    for i in range(len(obs)):
        obs[i] = {
            'dateTime': i * obs_frequency_in_sec,
            pollutant: readings[i % len(readings)]
        }
    return obs

def make_pairs(obs, pollutant):
    return list(map(lambda x: (x['dateTime'], x[pollutant]), obs))

class TestCalculatorCollection(unittest.TestCase):
    def test_get_last_valid_index(self):
        obs_frequency_in_sec = 600       # 10 minutes
        pollutant = O3
        for hours in [1, 2, 4, 5]:
            expected = int((hours * HOUR) / obs_frequency_in_sec) - 1
            obs = make_observations(pollutant, obs_frequency_in_sec, hours * HOUR)
            obs = sorted(obs, key=operator.itemgetter('dateTime'), reverse=True)
            obs = make_pairs(obs, pollutant)
            actual = get_last_valid_index(obs, hours * HOUR)
            self.assertEqual(actual, expected)

    def test_calculate(self):
        obs_frequency_in_sec = 600       # 10 minutes
        pollutant = O3
        obs_unit = 'parts_per_million'
        calculator = CalculatorCollection()
        calculator.add_calculator(
            LinearScale(
                unit=obs_unit,
                duration_in_secs=1 * HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=ROUND_TO_2,
                high_obs=10,
                breakpoints=[0, 34, 100, 150, 200]))
        calculator.add_calculator(
            LinearScale(
                unit=obs_unit,
                duration_in_secs=4 * HOUR,
                obs_frequency_in_sec=obs_frequency_in_sec,
                data_cleaner=ROUND_TO_2,
                high_obs=10,
                breakpoints=[0, 34, 100, 150, 200]))

        test_cases = [
            { 'hours': 1, 'expected': 35 },     # no 4 hour window
            { 'hours': 2, 'expected': 25 },     # no 4 hour window
            { 'hours': 4, 'expected': 30 },     # 4 hour > 1 hour
            { 'hours': 5, 'expected': 35 },     # 4 hour < 1 hour
        ]
        for tc in test_cases:
            obs = make_observations(pollutant, obs_frequency_in_sec, tc['hours'] * HOUR)
            actual_aqi = calculator.calculate(pollutant, obs_unit, obs)[0]
            self.assertEqual(actual_aqi, tc['expected'])

class TestBreakpointTable(unittest.TestCase):
    def test__calculate_index_from_mean(self):
        bpt = BreakpointTable(
            data_cleaner=TRUNCATE_TO_1,
            mean_cleaner=TRUNCATE_TO_1,
            unit='microgram_per_meter_cubed',
            duration_in_secs=3000,
            obs_frequency_in_sec=300) \
            .add_breakpoint(  0,  50,   0.0,  12.0) \
            .add_breakpoint( 51, 100,  12.1,  35.4) \
            .add_breakpoint(101, 150,  35.5,  55.4) \
            .add_breakpoint(151, 200,  55.5, 150.4) \
            .add_breakpoint(201, 300, 150.5, 250.4) \
            .add_breakpoint(301, 500, 250.5, 500.4)
        test_cases = [
            {'obs_mean':  0,   'expected': (  0, 0)},
            {'obs_mean':  6,   'expected': ( 25, 0)},
            {'obs_mean': 12,   'expected': ( 50, 0)},
            {'obs_mean': 12.1, 'expected': ( 51, 1)},
            {'obs_mean':200.45, 'expected': (250, 4)},
            {'obs_mean':500.4, 'expected': (500, 5)},
        ]
        for tc in test_cases:
            actual = bpt._calculate_index_from_mean(tc['obs_mean'])
            self.assertEqual(actual[0], tc['expected'][0])
            self.assertEqual(actual[1], tc['expected'][1])

        self.assertRaises(IndexError, bpt._calculate_index_from_mean, 501)

class TestLinearScale(unittest.TestCase):
    def test__calculate_index_from_mean(self):
        ls = LinearScale(unit='firkins', obs_frequency_in_sec=300, duration_in_secs=3000,
                         high_obs=10, breakpoints=[0,50,100,150,200])
        test_cases = [
            {'obs_mean':  0,   'expected': (  0, 0)},
            {'obs_mean':  2.5, 'expected': ( 25, 0)},
            {'obs_mean':  5,   'expected': ( 50, 1)},
            {'obs_mean': 10,   'expected': (100, 2)},
            {'obs_mean': 12,   'expected': (120, 2)},
            {'obs_mean': 20,   'expected': (200, 4)},
            {'obs_mean': 30,   'expected': (300, 4)},
        ]
        for tc in test_cases:
            actual = ls._calculate_index_from_mean(tc['obs_mean'])
            self.assertEqual(actual[0], tc['expected'][0])
            self.assertEqual(actual[1], tc['expected'][1])

        ls = LinearScale(unit='firkins', obs_frequency_in_sec=300, duration_in_secs=3000,
                         high_obs=10, high_aqi=200, breakpoints=[0,50,100,150,200])
        test_cases = [
            {'obs_mean':  0,   'expected': (  0, 0)},
            {'obs_mean':  2.5, 'expected': ( 50, 1)},
            {'obs_mean':  5,   'expected': (100, 2)},
            {'obs_mean': 10,   'expected': (200, 4)},
            {'obs_mean': 12,   'expected': (240, 4)},
            {'obs_mean': 20,   'expected': (400, 4)},
            {'obs_mean': 30,   'expected': (600, 4)},
        ]
        for tc in test_cases:
            actual = ls._calculate_index_from_mean(tc['obs_mean'])
            self.assertEqual(actual[0], tc['expected'][0])
            self.assertEqual(actual[1], tc['expected'][1])
