# weewx-aqi
# Copyright 2018 - Jonathan Koren <jonathan@jonathankoren.com>
# License: GPL 3

import weewx.units

import calculators

# molar masses (aka mollecular mass) in units of grams per mole
MOLAR_MASSES = {
    calculators.CO:   29.0101,  # carbon monoxide
    calculators.NO2:  46.0055,  # nitrogen dioxide
    calculators.SO2:  64.0638,  # sulfur dioxide
    calculators.O3:   47.9982,  # ozone
    calculators.NH3:  17.0305,  # methane
    calculators.PB:  207.2000,  # lead
}

GAS_CONSTANT = 8.31441  # in units of ((Pa m^3) / (K mol))
IDEAL_GAS_TEMP_IN_KELVIN = 298.15
IDEAL_GAS_PRESSURE_IN_PASCALS = 101325
MOLAR_VOLUME_AT_STAP_IN_LITERS = 24.4652

def convert_pollutant_units(pollutant, obs_value, obs_unit, required_unit, temp_in_kelvin, pressure_in_pascals):
    if obs_unit == required_unit:
        return obs_value

    if (obs_unit[:9] == 'part_per_') and required_unit.endswith('_per_meter_cubed'):
        if obs_unit == 'part_per_million':
            obs_value = convert_units(obs_value, obs_unit, 'part_per_billion', temp_in_kelvin, pressure_in_pascals)
            obs_unit = 'part_per_billion'
        v = ppb_to_microgram_per_meter_cubed(pollutant, obs_value, temp_in_kelvin, pressure_in_pascals)
        v_unit = 'microgram_per_meter_cubed'
        if required_unit == 'milligram_per_meter_cubed':
            return v / 1000.0
        else:
            return v
    elif (obs_unit[:9] == '_per_meter_cubed') and required_unit.endswith('part_per_'):
        if obs_unit == 'milligram_per_meter_cubed':
            obs_value *= 1000
            obs_unit = 'microgram_per_meter_cubed'
        v = microgram_per_meter_cubed_to_ppb(pollutant, obs_value, temp_in_kelvin, pressure_in_pascals)
        v_unit = 'part_per_billion'
        if required_unit == 'part_per_million':
            return v / 1000.0
        else:
            return v
    else:
        return weewx.units.conversionDict[obs_unit][required_unit](obs_value)

def molar_volume_in_litres(temp_in_kelvin, pressure_in_pascals):
    '''Calculates the molar volume of a gas at temperature and pressure according
    to the ideal gas law:

        V = (R * T) / P

    where:
        R is the gas constant
        T is temperature in kelvin
        P is pressure in pascals

    For reference, standard temperature and pressure is 298.15 Kelvin and 101325 Pascals.
    '''
    return round(GAS_CONSTANT * temp_in_kelvin / float(pressure_in_pascals), 4)

def ppb_to_microgram_per_meter_cubed(pollutant, ppb, sensor_temp_in_kelvin=IDEAL_GAS_TEMP_IN_KELVIN, sensor_pressure_in_pascals=IDEAL_GAS_PRESSURE_IN_PASCALS):
    '''Converts parts per billion to micrograms per cubic meters at temperature and pressure'''
    return round(ppb / (molar_volume_in_litres(sensor_temp_in_kelvin, sensor_pressure_in_pascals) * MOLAR_MASSES[pollutant]), 4)

def microgram_per_meter_cubed_to_ppb(pollutant, ug_per_m3, sensor_temp_in_kelvin=IDEAL_GAS_TEMP_IN_KELVIN, sensor_pressure_in_pascals=IDEAL_GAS_PRESSURE_IN_PASCALS):
    '''Converts parts per million to micrograms per cubic meters at temperature and pressure'''
    return round(molar_volume_in_litres(sensor_temp_in_kelvin, sensor_pressure_in_pascals) *  ug_per_m3 / MOLAR_MASSES[pollutant], 4)

# Define unit group for AQI columns
weewx.units.obs_group_dict['aqi_pm2_5'] = 'air_quality_index'
weewx.units.obs_group_dict['aqi_pm10']  = 'air_quality_index'
weewx.units.obs_group_dict['aqi_co']    = 'air_quality_index'
weewx.units.obs_group_dict['aqi_no2']   = 'air_quality_index'
weewx.units.obs_group_dict['aqi_so2']   = 'air_quality_index'
weewx.units.obs_group_dict['aqi_o3']    = 'air_quality_index'
weewx.units.obs_group_dict['aqi_nh3']   = 'air_quality_index'
weewx.units.obs_group_dict['aqi_pb']    = 'air_quality_index'

# define the units
weewx.units.USUnits['air_quality_index'] = 'air_quality_index'
weewx.units.MetricUnits['air_quality_index'] = 'air_quality_index'
weewx.units.MetricWXUnits['air_quality_index'] = 'air_quality_index'
weewx.units.default_unit_format_dict['air_quality_index'] = '%d'
weewx.units.default_unit_label_dict['air_quality_index'] = '' # unitless

# unit conversion
weewx.units.conversionDict['litre']['meter_cubed'] = lambda x: x / 1000.0
weewx.units.conversionDict['meter_cubed'] = { 'litre': lambda x: x * 1000.0 }
weewx.units.conversionDict['part_per_billion'] = { 'part_per_million': lambda x: x * 1000.0 },
weewx.units.conversionDict['part_per_million'] = { 'part_per_billion': lambda x: x / 1000.0 },
weewx.units.conversionDict['microgram_per_meter_cubed'] = { 'milligram_per_meter_cubed': lambda x: x / 1000.0 },
weewx.units.conversionDict['milligram_per_meter_cubed'] = { 'microgram_per_meter_cubed': lambda x: x * 1000.0 },
