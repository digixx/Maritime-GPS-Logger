import board
import busio
import digitalio
import time
import math
from m_io import create_thermalprinter

import vars
import datadb

Printer = create_thermalprinter()

GPS_INIT        = const(0)  # Initialize Logs and status
GPS_START       = const(1)  # print header and init logs
GPS_RECORDING   = const(2)  # collect data and print some data
GPS_SUMMARY     = const(3)  # calculate results and print summary

gps_new_day             = vars.Values(0)
gps_last_min            = vars.Values("na")
gps_last_hour           = vars.Values("na")
gps_last_quarter        = vars.Values("na")
gps_log_state           = vars.Values(GPS_INIT)
kml_filename            = vars.Values("na")
prn_subhead_interval    = vars.Values(0)

# GPS positions data buffer for 60min of data (1 min interval)
gpslog = datadb.Data_DB(60)
# GPS positions data buffer for 60h of data (1h interval)
gpslogsum = datadb.Data_DB(60)

# climate data buffer for 3h of data (3 min interval)
clilog = datadb.Data_DB(60)

def init_printer():
    if Printer.has_paper():
        print("Printer has paper!\n")
    else:
        print("Printer might be out of paper, or RX is disconnected")
    Printer.set_defaults()

def print_testpage():
    if Printer.has_paper():
        Printer.test_page()

def print_log_subheader():
    if prn_subhead_interval.value == 0:
        Printer.print("\nTIME      LATITUDE    LONGITUDE")
    else:
        Printer.print("")
    if prn_subhead_interval.value == 3:
        prn_subhead_interval.value = 0
    else:
        prn_subhead_interval.value += 1

def print_log_main_header(date, time):
    Printer.feed(3)
    Printer.bold = True
    Printer.double_width = True
    Printer.print("NAVIGATION - LOG")
    Printer.bold = False
    Printer.double_width = False

    data = ("DATE: {}  TIME: {}").format(date,time)
    Printer.print(data)
    print_log_subheader()

def print_log_data(date, time, lat, lon):
    data = "{}  {:010.6f}  {:010.6f}".format(time, lat, lon)
    Printer.print(data)

def print_log_small_summary(cog, sog, dist):
    data = "COG:{:3.0f} SOG:{:04.1f}kn DIST:{:05.2f}nm".format(cog, sog, dist)
    Printer.print(data)

def print_log_summery(triptime, avcog, avsog, dist):
    print('PrintLogSum', triptime, avcog, avsog, dist)
    if triptime > 0:
        hours = (triptime / 60)
        minutes = triptime % 60
    else:
        hours = 0
        minutes = 0

    Printer.bold = True
    data = "\nTOTAL  TIME: {:2.0f} h {:2.0f} min.".format(hours, minutes)
    Printer.print(data)
    data = "TOTAL  DIST: {:6.2f} nm".format(dist)
    Printer.print(data)
    data = "AVERAGE SOG: {:6.2f} kn".format(avsog)
    Printer.print(data)
    Printer.bold = False
    Printer.print("--------------------------------")
    Printer.feed(4)

def update_clilog(pressure, temperatur):
    clilog.add({"p": pressure, "t": temperatur})

def clear_climate_log():
    clilog.clear

def calc_3h_press_ratio():
    pmax = 0
    pmin = 2000
    pmaxpos = 0
    pminpos = 0
    l = len(clilog)

    if l < 4:
        return 0

    for x in range(0, l):
        p = clilog.get(x).get('p')
        # print('CLI-p:',p)
        if p >= pmax:
            pmax = p
            pmaxpos = x
        if p <= pmin:
            pmin = p
            pminpos = x

    pmaxv = clilog.get(pmaxpos).get('p')
    pminv = clilog.get(pminpos).get('p')
    # print('CLI-min-max:',pminv, pmaxv)
    ratio = pmaxv - pminv
    if pminpos > pmaxpos:
        ratio *= -1.0
    # print("3h ratio: ",ratio)
    return ratio

def calc_distance(coord1,coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371000 # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a),math.sqrt(1 - a))

    # meters = R * c # output distance in meters
    nauticalmiles = R * c / 1852
    return nauticalmiles

def calc_cog(coord1,coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371000 # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi_2)
    x = math.cos(phi_1) * math.sin(phi_2) - math.sin(phi_1) * math.cos(phi_2) * math.cos(delta_lambda)
    cog = (360 + math.degrees(math.atan2(y,x))) % 360
    return cog

def get_coord_from_gpslog(log, p):
    lat = log.get(p).get("lat")
    lon = log.get(p).get("lon")
    # print("CoordFromGPS:", lat, lon)
    return float(lat), float(lon)

def get_time_of_day(time):
    s = int(time[6:8])
    s += int(time[3:5]) * 60
    s += int(time[0:2]) * 3600
    # print("timeofday:", s)
    return s

def get_time_of_day_from_gpslog(log, p):
    if p < len(log):
        t = get_time_of_day(log.get(p).get("t"))
    return t

def get_trip_time(log):
    l = len(log)
    x = int((get_time_of_day_from_gpslog(log, l -1) - get_time_of_day_from_gpslog(log, 0)) / 60)
    return x

def get_dist_from_gpslog(log):
    distance = 0
    startpoint = 0
    l = len(log)
    if l > 1:
        for x in range(0, l-1):
            coord1 = get_coord_from_gpslog(log, x)
            coord2 = get_coord_from_gpslog(log, x + 1)
            # calculate distance between waypoints
            d1 = calc_distance(coord1, coord2)

            coord1 = get_coord_from_gpslog(log, startpoint)
            coord2 = get_coord_from_gpslog(log, x + 1)
            # calculate distance from start point
            d2 = calc_distance(coord1, coord2)

            """
            if d2 > 0.04: # if distance from startpoint exeeded 0.04 nm (~75m) add it to distance
                startpoint = x + 1 # make this coord the new startpoint for calculating the amount of movement
                print('New Startpoint in place:', startpoint)
            """
            distance += d1
            print("Distance:", x, d1, d2, "Total", distance)

        print("Distance Total:", distance, "Direct:", d2)
    return distance

def get_dist_from_gpslogsum(log):
    distance = 0
    l = len(log)
    if l > 1:
        for x in range(0, l):
            d2 = float(log.get(x).get("dist"))
            print("Distance2:", x, d2)
            distance += d2
    print("Distance2 Total:", distance)
    return distance

def detect_full_hour(time):
    result = False
    hour = time[0:2]
    if hour != gps_last_hour.value:
        gps_last_hour.value = hour
        result = True
    return result

def detect_new_min(time):
    result = False
    minute = time[3:5]
    if minute != gps_last_min.value:
        gps_last_min.value = minute
        result = True
    return result

def detect_new_quarter(time):
    result = False
    # quarters = "05,10,15,20,25,30,35,40,45,50,55,00"
    quarters = "15,30,45,00"
    minute = time[3:5]
    # print("Minute:", minute, quarters.find(minute))
    if quarters.find(minute) >= 0:
        if minute != gps_last_quarter.value:
            gps_last_quarter.value = minute
            result = True
    return result

def detect_new_day(time):
    result = False
    hour = time[0:2]
    if hour != gps_new_day.value:
        gps_new_day.value = hour
        if hour =="00":
            result = True
    return result

def handler_gpslog(rec, _gps, _sdc):
    if gps_log_state.value == GPS_INIT:
        if rec == 1: # Init Summary log
            gps_log_state.value = GPS_START
            print("GPS_Log: Init => Start")

    if gps_log_state.value == GPS_START:
        if _gps.is_valid:
            # Clear logs and save start position
            gpslogsum.clear
            gpslogsum.add({"d": _gps.date, "t": _gps.time, "lat": _gps.latitude_raw, "lon": _gps.longitude_raw, "dist": 0})
            gpslog.clear
            gpslog.add({"d": _gps.date, "t": _gps.time, "lat": _gps.latitude_raw, "lon": _gps.longitude_raw})

            gps_last_hour.value = _gps.time[0:2]
            gps_last_min.value = _gps.time[3:5]

            print_log_main_header(_gps.date, _gps.time)
            print_log_data(_gps.date, _gps.time, _gps.latitude_raw, _gps.longitude_raw)

            # create KML file
            kml_filename.value = _gps.reverse_date_kml
            _sdc.create_kml_file(kml_filename.value, "Track")

            gps_log_state.value = GPS_RECORDING
            print("GPS_Log: Start => Recording")

    if gps_log_state.value == GPS_RECORDING:
        if _gps.is_valid:
            if rec == 1:
                if detect_new_min(_gps.time):
                    print("GPS_Log: full minute detected")
                    gpslog.add({"d": _gps.date, "t": _gps.time, "lat": _gps.latitude_raw, "lon": _gps.longitude_raw})

                    # write GPS datas to SD-Card
                    _sdc.write_to_log(_gps.reverse_date + ".txt", _gps.date, _gps.time, _gps.latitude_log, _gps.longitude_log, _gps.speed)
                    _sdc.add_kml_data(kml_filename.value, _gps.latitude_log, _gps.longitude_log, _gps.altitude)

                    l = len(gpslog)
                    if l > 1:
                        triptime = get_trip_time(gpslog)
                        print("GPS_Log: TripTime:", triptime)

                if detect_new_quarter(_gps.time):
                    print("GPS_Log: quarter detected")
                    print_log_data(_gps.date, _gps.time, _gps.latitude_raw, _gps.longitude_raw)

                if detect_full_hour(_gps.time):
                    print("GPS_Log: full Hour detected")
                    distance = get_dist_from_gpslog(gpslog)
                    # add current position and distance to summary log
                    gpslogsum.add({"d": _gps.date, "t": _gps.time, "lat": _gps.latitude_raw, "lon": _gps.longitude_raw, "dist": distance})

                    l = len(gpslog)
                    if l > 1:
                        cog = calc_cog(get_coord_from_gpslog(gpslog, 0), get_coord_from_gpslog(gpslog, l - 1))
                        triptime = get_trip_time(gpslog)
                        print("Full Hour Triptime:", triptime)
                        sog = distance / (triptime / 60)
                    else:
                        sog = 0
                        cog = 0

                    print_log_small_summary(cog, sog, distance)
                    print_log_subheader()
                    gpslog.clear

                if detect_new_day(_gps.time):
                    print("GPS_Log: New Day detected")
                    # New Day
                    gps_log_state.value = GPS_SUMMARY
                    print("GPS_Log: Recording => Summary")

            else:
                # save last position
                gpslog.add({"d": _gps.date, "t": _gps.time, "lat": _gps.latitude_raw, "lon": _gps.longitude_raw})
                print_log_data(_gps.date, _gps.time, _gps.latitude_raw, _gps.longitude_raw)
                distance = get_dist_from_gpslog(gpslog)
                # save last position in log
                gpslogsum.add({"d": _gps.date, "t": _gps.time, "lat": _gps.latitude_raw, "lon": _gps.longitude_raw, "dist": distance})
                gps_log_state.value = GPS_SUMMARY
                print("GPS_Log: Recording => Summary")

    if gps_log_state.value == GPS_SUMMARY:
        print("GPS_Log: 'Print Summary'")
        distance = 0
        avcog = 0
        avsog = 0
        triptime = 0

        l = len(gpslogsum)
        if l > 1:
            distance = get_dist_from_gpslogsum(gpslogsum)
            avcog = calc_cog(get_coord_from_gpslog(gpslogsum, 0), get_coord_from_gpslog(gpslogsum, l - 1))
            triptime = get_trip_time(gpslogsum)
            if distance > 0 and triptime > 0:
                avsog = distance / (triptime / 60)
        
        print_log_summery(triptime, avcog, avsog, distance)
        _sdc.close_kml_file(kml_filename.value)
        gps_log_state.value = GPS_INIT
        print("GPS_Log: Summary => Init")

"""
    distance = 0
    l = len(GPSlog)
    if l > 1:
        for x in range(1, l):
            #start
            lon1 = float(GPSlog.get(x - 1).get("lon"))
            lat1 = float(GPSlog.get(x - 1).get("lat"))
            #stop
            lon2 = float(GPSlog.get(x).get("lon"))
            lat2 = float(GPSlog.get(x).get("lat"))
            distance += calcDistance([lat1, lon1], [lat2, llo2])
            print('GPS_Log:', x, [lat1, lon1], [lat2, lon2])

    print("Strecke=", distance)
"""

# Reinach       47.50998, 7.59646
# Gommiswald    47.23072, 9.00978

# d = calcDistance([47.50998,7.59646],[47.23072,9.00978])
# print("Distance = ", d)
