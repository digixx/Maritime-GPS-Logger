import adafruit_bmp280

class Sensor_BMP280:

    def __init__(self, spi, bmp_cs):
        self._bmp = adafruit_bmp280.Adafruit_BMP280_SPI(spi, bmp_cs)
        self._bmp.sea_level_pressure = 1013

    @property
    def sea_level_pressure(self, value):
        return self._bmp.sea_level_pressure

    @sea_level_pressure.setter
    def sea_level_pressure(self, value):
        self._bmp.sea_level_pressure = value

    @property
    def temp(self):
        return '%0.1f' % self._bmp.temperature

    @property
    def pressure(self):
        return '%0.1f' % self._bmp.pressure

    @property
    def pressure_hi_res(self):
        return self._bmp.pressure

    @property
    def temp_hi_res(self):
        return self._bmp.temperature

"""
ct = time.monotonic()

# Create the SPI bus
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
bmp_cs = digitalio.DigitalInOut(board.D5)
sensor = sensor_bmp280(spi, bmp_cs)
sensor.sea_level_pressure = 1013

while True:
    if ct + 0.5 < time.monotonic():
        ct = time.monotonic()
        print('Temp=', sensor.Temp)
        print('Press=', sensor.Pressure)
"""