import pulseio
import digitalio
import board
import time

class Sounds():

    SOUNDON = 2 ** 15
    SOUNDOFF = 0

    def __init__(self, pin):
        self._pin = pin
        self._lowfreq = 1000
        self._highfreq = 2000
        self._spkr = pulseio.PWMOut(pin, duty_cycle = self.SOUNDOFF, frequency = self._lowfreq, variable_frequency = True)

    def sound_on(self):
        self._spkr.duty_cycle = self.SOUNDON

    def sound_off(self):
        self._spkr.duty_cycle = self.SOUNDOFF

    def up(self, cycles = 1):
        self.sound_on()
        for _ in range(cycles):
            for x in range(self._lowfreq, self._highfreq):
                self._spkr.frequency = x
                time.sleep(0.0005)
        self.sound_off()

    def down(self, cycles = 1):
        self.sound_on()
        for _ in range(cycles):
            for x in range(self._highfreq, self._lowfreq, - 1):
                self._spkr.frequency = x
                time.sleep(0.0005)
        self.sound_off()

    def high_low(self, cycles):
        self.sound_on()
        for _ in range(cycles):
            self._spkr.frequency = self._highfreq
            time.sleep(0.15)
            self._spkr.frequency = self._lowfreq
            time.sleep(0.15)
        self.sound_off()

    def play_power_on_sound(self):
        self.sound_on()
        self._spkr.frequency = self._lowfreq
        time.sleep(0.25)
        self._spkr.frequency = self._highfreq
        time.sleep(0.25)
        self.sound_off()

    def play_gps_fix(self, mode):
        if mode > 0:
            self._spkr.frequency = self._lowfreq
            self.sound_on()
            time.sleep(0.15)
            self.sound_off()
            time.sleep(0.15)
            self.sound_on()
            time.sleep(0.15)
            self.sound_off()
        else:
            self._spkr.frequency = self._highfreq
            self.sound_on()
            time.sleep(0.15)
            self.sound_off()
            time.sleep(0.15)
            self.sound_on()
            time.sleep(0.15)
            self.sound_off()
