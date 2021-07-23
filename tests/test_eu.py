import unittest

from bin.user.aqi.eu import *

class TestEU(unittest.TestCase):
    def test_eu_24hr_mean(self):
        ''''''
        one_day_in_secs = 86400
        one_hour_in_secs = 3600
        expected_mean = 10
        obs_freq = 300
        obs_ratio = 0.75
        min_hours = 18

        def clean_obs(obs):
            ret = []
            for o in obs:
                if o is not None:
                    ret.append(o)
            return ret

        def gen_obs():
            readings = int(one_day_in_secs / obs_freq)
            obs = [None] * readings
            for r in range(readings):
                obs[r] = (r * obs_freq, expected_mean)
            return obs

        obs = gen_obs()
        self.assertEqual(eu_24hr_mean(obs, obs_freq, obs_ratio, min_hours), expected_mean)

        # now we're just checking for exceptions
        min_hours = 24
        # should pass
        eu_24hr_mean(obs, obs_freq, obs_ratio, min_hours)

        # Drop 1/12 of all observations, should stay good
        for i in range(len(obs)):
            if i % 12 == 0:
                obs[i] = None
        eu_24hr_mean(clean_obs(obs), obs_freq, obs_ratio, min_hours)

        # Drop 1/2 of all observations, should raise an exception
        for i in range(len(obs)):
            if i % 2 == 0:
                obs[i] = None
        self.assertRaises(ValueError, eu_24hr_mean, clean_obs(obs), obs_freq, obs_ratio, min_hours)

        # drop half the observations, but only from the first six hours, this should be good
        obs = gen_obs()
        for i in range(len(obs)):
            if i < (6 * (one_hour_in_secs / obs_freq)):
                if i % 2 == 0:
                    obs[i] = None
        obs = clean_obs(obs)
        min_hours = 18
        eu_24hr_mean(obs, obs_freq, obs_ratio, min_hours)

        # Drop 1/2 of all observations through truncation, should raise an exception
        obs = gen_obs()[:int(one_day_in_secs / obs_freq / 2)]
        min_hours = 18
        self.assertRaises(ValueError, eu_24hr_mean, obs, obs_freq, obs_ratio, min_hours)
