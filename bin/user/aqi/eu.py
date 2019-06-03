# weewx-aqi
# Copyright 2018, 2019 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

import datetime
import operator
import syslog

import calculators
import standards

# colors taken from https://www.eea.europa.eu/themes/air/air-quality-index/index
COLOR_GOOD = '4FECE2'
COLOR_FAIR = '50CCAA'
COLOR_MODERATE = 'F0E641'
COLOR_POOR = 'FF5050'
COLOR_VERY_POOR = '960032'

def get_cams_value(pollutant):
    raise NotImplementedError('CAMS fetching is not supported at this time.')

def eu_mean(observations, obs_frequency_in_sec, actual_time_range_seconds, required_observation_ratio, pollutant):
    # we have to do validate the actual time range, as upstream only
    # validated the much larger fake range
    now_epoch_seconds = observations[0][0]
    min_samples_per_hour = int(calculators.HOUR / float(obs_frequency_in_sec) * required_observation_ratio)

    # calculate the hourly averages, flagging any hours that don't have enough
    # samples
    hourly_averages = [0] * 4 * 24
    hourly_samples = [0] * 4 * 24
    now_epoch_hour = now_epoch_seconds / calculators.HOUR
    for observation in observations:
        hours_ago = now_epoch_hour - (observation[0] / calculators.HOUR)
        hourly_averages[hours_ago] += observation[1]
        hourly_samples[hours_ago] += 1
    for i in range(len(hourly_samples)):
        if hourly_samples[i] < min_samples_per_hour:
            hourly_averages[i] = -1
        else:
            hourly_averages[i] / float(hourly_samples[i])

    # check the last 24 hours to see if we're good
    for i in range(24):
        if hourly_averages[i] < 0:
            # recent data is missing, check previous days
            correction_factor = 0
            count = 0
            for j in range(1, 5):
                if hourly_averages[i + (24 * j)] == -1:
                    continue
                count += 1
                then_epoch_seconds = now - (i * calculators.HOUR) - (j * calculators.DAY)
                cams_value = fetch_cams(pollutant, then_epoch_seconds)
                if pollutant == calculators.NO2
                    or pollutant == calculators.PM2_5
                    or pollutant == calculators.PM10_0:
                    correction_factor += hourly_averages[i + (24 * j)] - cams_value
                elif pollutant == calculators.O3:
                    correction_factor += hourly_averages[i + (24 * j)] / cams_value
                else:
                    raise ValueError('Can not be estimate missing data')
            if count < 3:
                raise ValueError('Can not be estimate missing data')

            correction_factor /= float(count)
            then_epoch_seconds = now - (i * calculators.HOUR)
            cams_value = fetch_cams(pollutant, then_epoch_seconds)

            if pollutant == calculators.NO2
                or pollutant == calculators.PM2_5
                or pollutant == calculators.PM10_0:
                hourly_averages[i] = cams_value + correction_factor
            elif pollutant == calculators.O3:
                hourly_averages[i] = cams_value * correction_factor
            else:
                raise ValueError('Can not be estimate missing data')



def fetch_cams(pollutant, epoch_seconds):
    raise NotImplementedError("Don't know how to fetch CAMS data")

    # FIXME: Check the CAMS cache. If it's there, return it, else
    # FIXME






def get_cams_url(pollutant, epoch_seconds):
    '''http://atmosphere.copernicus.eu/ftp-access-global-data'''

    # WMO location codeself.
    # See http://www.wmo.int/pages/prog/www/ois/Operational_Information/VolumeC1/CCCC_en.pdf
    # Examples:
    #   KSJC -- San Jose California
    #   BGSF -- Søndre Strømfjord, Greenland

    wmo_location_code = 'KPAH' # FIXME: some how this has to come from configuration
    time_directory = datetime.datetime.fromtimestamp(epoch_seconds).strftime("%Y%m%d%H")
    time_file = datetime.datetime.fromtimestamp(epoch_seconds).strftime("%Y%m%d%H%M%S")

    product_type = 'an' # FIXME: confirm fc = forecast, an = analysis
    level_filed = 'sfc' # FIXME: configm sfc = surface, pl = pressure level, ml = model level
    forecast_end_hour = int(datetime.datetime.fromtimestamp(epoch_seconds).strftime("%H")) + 1
    # See

    param = None
    if pollutant == calcualtors.PM2_5:
        param = 'pm2p5' # kg m-3
    elif pollutant == calcualtors.PM10_0:
        param = 'pm10'  # kg m-3
    elif pollutant == calcualtors.NO2:
        raise NotImplementedError()
    elif pollutant == calcualtors.O3:
        raise NotImplementedError()
    else:
        raise ValueError('Can not fetch pollutant %s' % (pollutant))

     filename = 'z_cams_c_%s_%s_prod_%s_%s_%03d_%s.nc' % (
        wmo_location_code.lower(),
        time_file,
        product_type,
        forecast_end_hour,
        param,
     )


    # http://atmosphere.copernicus.eu/ftp-access-global-data
    # https://download.regional.atmosphere.copernicus.eu/services/CAMS50?token=__M0bChV6QsoOFqHz31VRqnpr4GhWPtcpaRy3oeZjBNSg__&grid=0.1&model=ENSEMBLE&package=ANALYSIS_CO_ALLLEVELS&time=-24H-1H&referencetime=2018-05-25T00:00:00Z&format=NETCDF&licence=yes
    #



     wmo_location_code = 'KPAH'
     user = 'USERNAME'       # FIXME
     password = 'PASSWORD'   # FIXME
     url = 'ftp://%s:%s@dissemination.ecmwf.int/DATA/CAMS_NREALTIME/%s/%s' % (
         user,
         password,
         wmo_location_code.upper(),
         filename
     )

'


# For NO2, O3 and SO2 , hourly concentrations of NO2, O3 and SO2 are used for the
# calculation of the index. For PM10 and PM2.5, the 24-hour running means, based
# on the last 24 hours, are considered for the calculation of the index.
# Missing data and gap filling
#
# When data from countries has not been reported for a given hour, values are
# approximated ('gap-filled') using CAMS modelled air quality data. In such
# cases, it is clearly marked within the Index as being 'modelled data'.
#
# The gap-filling method used depends on the pollutant, i.e.
#
#     for NO2, PM2.5 and PM10 by using a difference method;
#     for O3 by using a multiplicative method;
#     for SO2 no gap filling is performed
#
# Difference method: the value is approximated by taking the CAMS modelled value,
# and adding or subtracting a correction difference. This correction is the
# average difference between previously measured values and the CAMS modelled
# value for the same hour for at least three of the four previous days
#
# Multiplicative method: the value is approximated by taking the CAMS modelled
# value, and applying a correction factor. This correction is the average ratio
# between the previously measured values and the CAMS modelled values for the
# same hour for at least three of the four previous days.


class AirQualityIndex(standards.AqiStandards):
    '''Calucates the European Union's Air Quality Index, as explained in
    https://www.eea.europa.eu/themes/air/air-quality-index/index .
    Interestingly, the EU does not define a a numeric value for the AQI, but
    rather refers only to categorical labels. For purposes in weewx-aqi,
    we assign each label an integer starting at 1 for "Good", and ending with
    5 for "Very Poor".'''

    def __init__(self, obs_frequency_in_sec):
        super(AirQualityIndex, self).__init__(
            [COLOR_GOOD, COLOR_FAIR, COLOR_MODERATE, COLOR_POOR, COLOR_VERY_POOR],
            ['Good', 'Fair', 'Moderate', 'Poor', 'Very Poor'],
            7)

        self.calculators[calculators.PM2_5] = calculators.AqiTable()
        self.calculators[calculators.PM2_5].add_breakpoint_table(calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_1,
            mean_calculator=lambda obs: eu_mean(obs, obs_frequency_in_sec, 0.75, 24 * calculators.HOUR, calculators.PM2_5),
            unit='microgram_per_meter_cubed',
            duration_in_secs=5 * calculators.DAY,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,  0.0,  10) \
            .add_breakpoint( 2,  2, 10.1,  20) \
            .add_breakpoint( 3,  3, 20.1,  25) \
            .add_breakpoint( 4,  4, 25.1,  50) \
            .add_breakpoint( 5,  5, 50.1, 800))

        self.calculators[calculators.PM10_0] = calculators.AqiTable()
        self.calculators[calculators.PM10_0].add_breakpoint_table(calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_1,
            unit='microgram_per_meter_cubed',
            mean_calculator=lambda obs: eu_mean(obs, obs_frequency_in_sec, 0.75, 24 * calculators.HOUR, calculators.PM10_0),
            duration_in_secs=5 * calculators.DAY,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,   0.0,    20) \
            .add_breakpoint( 2,  2,  20.1,    35) \
            .add_breakpoint( 3,  3,  35.1,    50) \
            .add_breakpoint( 4,  4,  50.1,   100) \
            .add_breakpoint( 5,  5,  100.1, 1200))

        self.calculators[calculators.NO2] = calculators.AqiTable()
        self.calculators[calculators.NO2].add_breakpoint_table(calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_1,
            unit='microgram_per_meter_cubed',
            mean_calculator=lambda obs: eu_mean(obs, obs_frequency_in_sec, 0.75, 1 * calculators.HOUR, calculators.NO2),
            duration_in_secs=5 * calculators.DAY,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,   0.0,   40) \
            .add_breakpoint( 2,  2,  40.1,  100) \
            .add_breakpoint( 3,  3, 100.1,  200) \
            .add_breakpoint( 4,  4, 200.1,  400) \
            .add_breakpoint( 5,  5, 400.1, 1000))

        self.calculators[calculators.O3] = calculators.AqiTable()
        self.calculators[calculators.O3].add_breakpoint_table(calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_1,
            unit='microgram_per_meter_cubed',
            mean_calculator=lambda obs: eu_mean(obs, obs_frequency_in_sec, 0.75, 1 * calculators.HOUR, calculators.O3),
            duration_in_secs=5 * calculators.DAY,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,    0.0,  80) \
            .add_breakpoint( 2,  2,   80.1, 120) \
            .add_breakpoint( 3,  3,  120.1, 180) \
            .add_breakpoint( 4,  4,  180.1, 240) \
            .add_breakpoint( 5,  5,  240.1, 600))

        self.calculators[calculators.SO2] =  calculators.AqiTable()
        self.calculators[calculators.SO2].add_breakpoint_table(calculators.BreakpointTable(
            mean_cleaner=calculators.ROUND_TO_1,
            unit='microgram_per_meter_cubed',
            mean_calculator=lambda obs: eu_mean(obs, obs_frequency_in_sec, 0.75, 1 * calculators.HOUR, calculators.SO2),
            duration_in_secs=5 * calculators.DAY,
            obs_frequency_in_sec=obs_frequency_in_sec) \
            .add_breakpoint( 1,  1,    0.0,  100) \
            .add_breakpoint( 2,  2,  100.1,  200) \
            .add_breakpoint( 3,  3,  200.1,  350) \
            .add_breakpoint( 4,  4,  350.1,  500) \
            .add_breakpoint( 5,  5,  500.1, 1250))
