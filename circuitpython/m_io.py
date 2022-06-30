import os
import board
import busio
import digitalio
import neopixel
from sdcard import SDCard
from sounds import Sounds
from sensors import Sensor_BMP280
from gps import GPS
from adafruit_thermal_printer import ThermalPrinter

heartbeat = digitalio.DigitalInOut(board.A2)
heartbeat.direction = digitalio.Direction.OUTPUT
heartbeat.value = True

NEOpix = neopixel.NeoPixel(board.NEOPIXEL, 1)
# set color to green
NEOpix[0] = (0, 1, 0)

# Create the SPI bus for multiple devices
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

def do_heart_beat():
    # toggle LED
    heartbeat.value = not heartbeat.value

def create_sensors():
    bmp_cs = digitalio.DigitalInOut(board.D5)
    sensors = Sensor_BMP280(spi, bmp_cs)
    sensors.sea_level_pressure = 1013
    return sensors

def create_sdcard():
    sd_cs = digitalio.DigitalInOut(board.D9)
    sd_cd = digitalio.DigitalInOut(board.D6)
    sd_root = '/sd'
    sdc = SDCard(spi, sd_cs, sd_cd, sd_root)
    return sdc

def create_gps():
    gps_uart = busio.UART(board.D12, board.D11, baudrate=9600, timeout=20, receiver_buffer_size=256)
    gps = GPS(gps_uart)
    return gps

def create_thermalprinter():
    printer_uart = busio.UART(board.SDA, board.SCL, baudrate=19200, timeout=20)
    printer = ThermalPrinter(printer_uart)
    return printer

def create_speaker():
    spkr = Sounds(board.D13)
    return spkr
