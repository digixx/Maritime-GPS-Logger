import adafruit_gps_mod

class GPS:

    def __init__(self, uart):
        self._gps = adafruit_gps_mod.GPS(uart, debug = False)
        # Initialize the GPS module by changing what data it sends and at what rate.
        # These are NMEA extensions for PMTK_314_SET_NMEA_OUTPUT and
        # PMTK_220_SET_NMEA_UPDATERATE but you can send anything from here to adjust
        # the GPS module behavior:
        #   https://cdn-shop.adafruit.com/datasheets/PMTK_A11.pdf

        # Set update rate to once a second (1hz) which is what you typically want.
        # gps.send_command(b'PMTK220,1000')
        # Or decrease to once every two seconds by doubling the millisecond value.
        # Be sure to also increase your UART timeout above!
        self._gps.send_command(b'PMTK220,1000') # first command is lost !!
        self._gps.send_command(b'PMTK220,500')

        # Turn on the basic GGA and RMC info (what you typically want)
        self._gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

        # Turn on AIC (Active Interference Cancellation)
        self._gps.send_command(b'PMTK286,1')

    def update(self):
        self._gps.update()

    @property
    def is_valid(self):
        return self._gps.valid

    @property
    def fix(self):
        return self._gps.fix_quality

    @property
    def fix_3d(self):
        if self._gps.valid:
            return self._gps.fix_quality_3d
        else:
            return 0

    @property
    def satellites(self):
        data_str = "-"
        if self._gps.satellites is not None:
            data_str = '{}'.format(self._gps.satellites)
        return data_str

    @property
    def hdilution(self):
        data_str = "-"
        if self._gps.horizontal_dilution is not None:
            data_str = '{}'.format(self._gps.horizontal_dilution)
        return data_str

    @property
    def geoid_height(self):
        data_str = "-"
        if self._gps.height_geoid is not None:
            data_str = '{}'.format(self._gps.height_geoid)
        return data_str

    @property
    def date(self):
        data_str = '{:02}.{:02}.{:04}'.format(
        self._gps.timestamp_utc.tm_mday,  # Grab parts of the time from the
        self._gps.timestamp_utc.tm_mon,   # struct_time object that holds
        self._gps.timestamp_utc.tm_year)  # the fix time.  Note you might
        return data_str

    @property
    def reverse_date(self):
        data_str = '{:04}_{:02}_{:02}'.format(
        self._gps.timestamp_utc.tm_year,  # the fix time.  Note you might
        self._gps.timestamp_utc.tm_mon,   # struct_time object that holds
        self._gps.timestamp_utc.tm_mday)  # Grab parts of the time from the
        return data_str

    @property
    def reverse_date_kml(self):
        data_str = '{:04}_{:02}_{:02}_{:02}-{:02}'.format(
        self._gps.timestamp_utc.tm_year,  # the fix time.  Note you might
        self._gps.timestamp_utc.tm_mon,   # struct_time object that holds
        self._gps.timestamp_utc.tm_mday,  # Grab parts of the time from the
        self._gps.timestamp_utc.tm_hour,  # not get all data like year, day,
        self._gps.timestamp_utc.tm_min)   # month!
        return data_str        

    @property
    def time(self):
        data_str = '{:02}:{:02}:{:02}'.format(
        self._gps.timestamp_utc.tm_hour,  # not get all data like year, day,
        self._gps.timestamp_utc.tm_min,   # month!
        self._gps.timestamp_utc.tm_sec)
        return data_str

    @property
    def latitude(self):
        if self._gps.latitude > 0:
            Deg = '{:d}'.format(int(self._gps.latitude))
            Min = '{0:.3f}'.format((self._gps.latitude % 1) * 60)
            NS = "N"
        else:
            Deg = '{:d}'.format(int(self._gps.latitude * -1))
            Min = '{0:.3f}'.format(((self._gps.latitude * -1) % 1) * 60)
            NS = "S"
        return Deg,Min,NS

    @property
    def longitude(self):
        if self._gps.longitude > 0:
            Deg = '{:d}'.format(int(self._gps.longitude))
            Min = '{0:.3f}'.format((self._gps.longitude % 1) * 60)
            EW = "E"
        else:
            Deg = '{:d}'.format(int(self._gps.longitude * -1))
            Min = '{0:.3f}'.format(((self._gps.longitude * -1) % 1) * 60)
            EW = "W"
        return Deg,Min,EW

    @property
    def latitude_log(self):
        data_str = '{0:.6f}'.format(self._gps.latitude)
        return data_str

    @property
    def longitude_log(self):
        data_str = '{0:.6f}'.format(self._gps.longitude)
        return data_str

    @property
    def latitude_raw(self):
        return self._gps.latitude

    @property
    def longitude_raw(self):
        return self._gps.longitude

    @property
    def speed(self):
        data_str = "-"
        if self._gps.speed_knots is not None:
            data_str = '{0:.1f}'.format(self._gps.speed_knots)
        return data_str

    @property
    def course(self):
        data_str = "-"
        if self._gps.track_angle_deg is not None:
            if self._gps.speed_knots > 1:
                data_str = '{0:.0f}'.format(self._gps.track_angle_deg)
        return data_str

    @property
    def altitude(self):
        data_str = "-"
        if self._gps.altitude_m is not None:
            data_str = '{}'.format(self._gps.altitude_m)
        return data_str

"""
ct = time.monotonic()
uart = busio.UART(board.D12, board.D11, baudrate=9600, timeout=20)
myGPS = gps(uart)

while True:
    if ct + 0.5 < time.monotonic():
        ct = time.monotonic()
        myGPS.update()
        print(myGPS.Fix)

"""