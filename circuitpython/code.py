import board
import busio
import digitalio
import time

import events
import vars

import m_nextion
import m_io
import m_data

# Display
Nextion_LED = m_nextion.create_led()
Nextion_UI = m_nextion.create_nextion()

# Loudspeaker
SPKR = m_io.create_speaker()

# GPS Module
GPS = m_io.create_gps()

# Sensors
Sensors = m_io.create_sensors()

# SD Card
SDC = m_io.create_sdcard()
if SDC.available():
	SDC.create_dir('/logs')
	SDC.create_dir('/kml')
	SDC.list_dir()
	# SDC.list_dir('/logs')
	# SDC.list_dir('/kml')
	print("Free:", SDC.get_free_space(), "MB")
	print('\n')
else:
	print('no Card found\n')

# Declare Events
ev500msec = events.Events(0.5)
ev1sec = events.Events(1)
ev5sec = events.Events(5)
ev1min = events.Events(60)
ev3min = events.Events(180)

# Global vars
gps_fix_status = vars.Values("0")

SPKR.play_power_on_sound()

# run main loop
while True:
	tstart = time.monotonic()
	GPS.update()
	m_nextion.update(Nextion_UI, Nextion_LED)
	tstop = time.monotonic()
	if tstop - tstart > 0.5:
		print("Update overload")

	if ev500msec.is_due:
		m_io.do_heart_beat()
		Nextion_UI.set_element("satfix", GPS.fix_3d)
		Nextion_UI.set_element("cTemp", Sensors.temp)
		Nextion_UI.set_element("cPress", Sensors.pressure)
		Nextion_UI.set_element("nTemp", Sensors.temp_hi_res * 10)
		m_data.handler_gpslog(Nextion_UI.get_element("b3"), GPS, SDC)

		if GPS.is_valid:
			Nextion_UI.set_element("cDate", GPS.date)
			Nextion_UI.set_element("cTime", GPS.time)

			Deg, Min, NS = GPS.latitude
			Nextion_UI.set_element("cLatDeg", Deg)
			Nextion_UI.set_element("cLatMin", Min)
			Nextion_UI.set_element("cLatNS", NS)

			Deg, Min, EW = GPS.longitude
			Nextion_UI.set_element("cLonDeg", Deg)
			Nextion_UI.set_element("cLonMin", Min)
			Nextion_UI.set_element("cLonEW", EW)

			Nextion_UI.set_element("cSOG", GPS.speed)
			Nextion_UI.set_element("cCOG", GPS.course)

			Nextion_UI.set_element("cSat", GPS.satellites)
			Nextion_UI.set_element("cAlt", GPS.altitude)
			Nextion_UI.set_element("cHDil", GPS.hdilution)
			Nextion_UI.set_element("cGH", GPS.geoid_height)

		if Nextion_UI.get_element("b0") == 1:
			m_data.print_testpage()
			Nextion_UI.set_element("b0", 0)
			print("Printer: print Testpage")

	if ev1sec.is_due:
		if gps_fix_status.has_changed(GPS.fix > 0):
			# SPKR.play_gps_fix(GPS.fix)
			print("GPS-Fix:", GPS.fix)

	if ev5sec.is_due:
		pass #print("5sec Event")

	if ev1min.is_due:
		# Alarm Temp High
		if Nextion_UI.get_element("a1") == 1:
			SPKR.up(2)
			Nextion_UI.set_element("a1", 0)
			print("Alert: Temp to high")

        # Alarm Temp Low
		if Nextion_UI.get_element("a2") == 1:
			SPKR.down(2)
			Nextion_UI.set_element("a2", 0)
			print("Alert: Temp to low")

        # Alarm Storm
		if Nextion_UI.get_element("r3") == 1:
			# Clear PressureData
			m_data.clear_climate_log()
			Nextion_UI.set_element("a3", 0)
			Nextion_UI.set_element("r3", 0)
			print("Alert: Storm cleared")

		if Nextion_UI.get_element("a3") == 1:
			SPKR.high_low(3)
			Nextion_UI.set_element("a3", 0)
			print("Alert: Storm")

		if GPS.is_valid:
			if Nextion_UI.get_element("b3") == 1:
				SDC.write_to_log(GPS.reverse_date + ".txt", GPS.date, GPS.time, GPS.latitude_log, GPS.longitude_log, GPS.speed)

	if ev3min.is_due:
		m_nextion.update_climate_graph(Nextion_UI, Sensors.pressure, Sensors.temp)
		m_data.update_clilog(Sensors.pressure_hi_res, Sensors.temp_hi_res)
		Nextion_UI.set_element("cPress3h", '%0.1f' % m_data.calc_3h_press_ratio())
		Nextion_UI.set_element("nPress3h", int(m_data.calc_3h_press_ratio() * 10))
		Nextion_UI.set_element("SDCfree", '%s' % SDC.get_free_space())
