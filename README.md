# weewx-aqi
Copyright 2018, 2019 - Jonathan Koren <jonathan@jonathankoren.com>

## What is it?
`weewx-aqi` *is not* an air quality monitor. Instead, it calculates an air
quality index from various pollutants. Air quality indices are single numbers
that are meant to succinctly describe how safe the air is. `weeex-aqi` can
calculate the following indices:

* Australia's Air Quality Index
* Australia's Interim Web Reporting Particulate Index (February 2020)
* Canada's Air Quality Health Index
* European Union's European Air Quality Index
* European Union's Common Air Quality Hourly Index
* India's National Air Quality Index
* Mexico's Índice Metropolitano de la Calidad del Aire
* United Kingdom's Daily Air Quality Index
* United States's Air Quality Index
* United States's NowCast Air Quality Index


## Prerequisites
A source for air quality data, such as
[`weewx-purpleair`](https://github.com/bakerkj/weewx-purpleair) .


## Installation
1) run the installer (from the git directory):

    wee_extension --install .

2) restart weewx:

    sudo /etc/init.d/weewx stop
    sudo /etc/init.d/weewx start

This will install the extension into the weewx/user/ directory.  

By default, the install script configures `weewx-aqi` for use with
`weewx-purpleair` and calculates a United States's NowCast AQI. If you are not
using `weewx-purpleair`, or wish to use a different air quality index, you will
need to modify your `weewx.conf`.

When configuring a different air quality sensor, you need to set the
`data_binding` of sensor readings, and provide a schema of columns to pollutants.
along with a column storing the reading's timestamp in epoch seconds UTC, and
a column with the semantics of WeeWx's `usUnits`. Optional columns for
temperature, and atmospheric pressure are helpful, but not required.

The configurable schema columns are:
* `dateTime`: *required* Timestamp of the reading in epoch seconds UTC.
* `usUnits`: *required* Unit system the readings are stored in.
* `temp`: *optional* Temperature at the sensor.
* `pressure`: *optional* Atmospheric at the sensor.
* `pm2_5`:  *optional* Particulate matter smaller than 2.5 micrometers
* `pm10_0`:  *optional* Particulate matter smaller than 10 micrometers
* `co`:  *optional* Carbon monoxide
* `no2`:  *optional* Nitrogen dioxide
* `so2`:  *optional* Sulfur dioxide
* `o3`:  *optional* Ozone
* `nh3`:  *optional* Ammonia
* `pb`:  *optional* Lead

All air quality indices, with the exception of Canada's, can be calculated
for a single pollutant. Additionally, all air quality indices can also
calculate composite index. However, this index will only be calculated if
readings are available for all of the requisite components.

After installation, you will need to modify your `weewx.conf`. Mainly, you will
need to connect `weewx-aqi` to the data binding for the air sensor. Assuming
you're using `weewx-purpleair`, you will need to add the following to your
`weewx.conf`.

The default `weewx.conf` block is:
```
[AqiService]
    [[air_sensor]]
        pm2_5 = pm2_5_atm
        temp = purple_temperature
        data_binding = purpleair_binding
        dateTime = dateTime
        pressure = purple_pressure
        pm10_0 = pm10_0_atm
        usUnits = usUnits
    [[standard]]
        data_binding = aqi_binding
        standard = user.aqi.us.NowCast
```

## Display the data
To make use of the plugin you will need to modify the templates in
`/etc/weewx/skins/*.tmpl` to include references to the new data found in
the aqi.sdb file.

### Examples:
#### The Current Value
`$latest($data_binding='aqi_binding').aqi_pm2_5`

#### Maximum Value Today
`$day($data_binding='aqi_binding').aqi_pm2_5.max`

#### Time Today When The Maximum Value Occurred
`$day($data_binding='aqi_binding').aqi_pm2_5.maxtime`

#### Colors and Categories
AQIs have categorical labels associated with the AQI values. The index of the
current category is available via `$latest($data_binding='aqi_binding').aqi_pm2_5_category`.
The AQI color and category can be found using wrapping the index with the`$aqi`
Cheetah template. Add to your `skin.conf`:
```
[CheetahGenerator]
    search_list_extensions = user.aqi.service.AqiSearchList
```
And then in your template (e.g. `index.html.tmpl`), you can add something
similar to this example `<DIV>`, that illustrates display the AQI value,
category, and color:
```
<div style="text-align: center; background-color: #$aqi($current($data_binding='aqi_binding').aqi_pm2_5_category).color;" >
    $current($data_binding='aqi_binding').aqi_pm2_5 <br/>
    $aqi($current($data_binding='aqi_binding').aqi_pm2_5_category).category
</div>
```

## Units
AQIs are dimensionless.

You can also graph these values by adding the appropriate
configuration to your `skin.conf` file:
```
    [[[dayaqi]]]
        data_binding = aqi_binding
        [[[[aqi_pm2_5]]]]
```

The values stored in the database are:
```
aqi_composite,
aqi_composite_category,
aqi_pm2_5,
aqi_pm2_5_category,
aqi_pm10_0,
aqi_pm10_0_category,
aqi_co,
aqi_co_category,
aqi_no2,
aqi_no2_category,
aqi_so2,
aqi_so2_category,
aqi_o3,
aqi_o3_category,
aqi_nh3,
aqi_nh3_category,
aqi_pb,
aqi_pb_category,
```

## Additional utilities
`aqi_backfill` is a utility that allows you to backfill `aqi.sdb` according to
the current `weewx.conf`.


## Development Testing
```
cd weewx-aqi
python3 -m unittest
```
