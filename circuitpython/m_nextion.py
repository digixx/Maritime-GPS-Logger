import board
import busio
import digitalio
from nextion import Nextion


def create_led():
    led = digitalio.DigitalInOut(board.A3)
    led.direction = digitalio.Direction.OUTPUT
    led.value = True
    return led


def toggle_led(led):
    led.value = not led.value


def create_nextion():
    uart = busio.UART(board.TX, board.RX, stop=1, baudrate=115200, timeout=0.1)
    nextion = Nextion(uart)

    # **** String Elements
    # GPS
    nextion.add_element("cDate", "--.--.--")
    nextion.add_element("cTime", "--.--.--")

    nextion.add_element("cLatDeg", "--")
    nextion.add_element("cLatMin", "--.---")
    nextion.add_element("cLatNS", "-")

    nextion.add_element("cLonDeg", "--")
    nextion.add_element("cLonMin", "--.---")
    nextion.add_element("cLonEW", "-")

    nextion.add_element("cSOG", "-")
    nextion.add_element("cCOG", "-")
    nextion.add_element("cSat", "-")
    nextion.add_element("cAlt", "-")
    nextion.add_element("cHDil", "-")
    nextion.add_element("cGH", "-")

    # Sensors
    nextion.add_element("cTemp", "-")
    nextion.add_element("cPress", "-")
    nextion.add_element("cPress3h", "-")
    nextion.add_element("p2txt", "-")

    # SD Card
    nextion.add_element("SDCfree", "-")
    nextion.add_element("SDCdir", "-")
    nextion.add_element("SDCfiles", "-")

    # **** Integer Elements

    # internal
    nextion.add_element("sys0", 0)
    nextion.add_element("sys1", 0)
    nextion.add_element("sys2", 0)

    # GPS
    nextion.add_element("satfix", 0)
    nextion.add_element("GPSrec", 0)

    # Sensors
    nextion.add_element("nTemp", 0)
    nextion.add_element("nPress3h", 0)

    # **** Button Elements
    nextion.add_element("b0", 0)  # Print Testpage
    nextion.add_element("b3", 0)  # GPS recording

    # **** Alert Elements
    nextion.add_element("a1", 0)  # Temp low alarm
    nextion.add_element("a2", 0)  # Temp high alarm
    nextion.add_element("a3", 0)  # Storm alarm
    nextion.add_element("r3", 0)  # Storm alarm reset

    return nextion


def refresh_page_data(nextion, page, part):
    #print("Page:", page, part)
    if page == "1":  # Main screen showing GPS data
        nextion.refresh_element("cTime")

        nextion.refresh_element("cDate")
        nextion.refresh_element("satfix")

        nextion.refresh_element("cLatDeg")
        nextion.refresh_element("cLatMin")
        nextion.refresh_element("cLatNS")

        nextion.refresh_element("cLonDeg")
        nextion.refresh_element("cLonMin")
        nextion.refresh_element("cLonEW")

        nextion.refresh_element("cCOG")
        nextion.refresh_element("cSOG")

        nextion.refresh_element("cTemp")
        nextion.refresh_element("cPress")

        nextion.refresh_element("nTemp")
        nextion.refresh_element("nPress3h")

        nextion.set_element("GPSrec", nextion.get_element("b3"), True)

    elif page == "2":  # info screen
        if part == "0":
            text = (
                "*** GPS ***\\r"
                "Datum:     {}\\r"
                "Zeit UTC:  {}\\r"
                "Lat:       {}.{} {}\\r"
                "Lon:       {}.{} {}\\r"
                "Geschwind.:{} kn\\r"
                "Kurs:      {} °\\r"
                "Satelliten:{}\\r"
                "Hoehe:     {} m\\r"
                "Fix:       {}\\r"
            ).format(
                nextion.get_element("cDate"),
                nextion.get_element("cTime"),
                nextion.get_element("cLatDeg"),
                nextion.get_element("cLatMin"),
                nextion.get_element("cLatNS"),
                nextion.get_element("cLonDeg"),
                nextion.get_element("cLonMin"),
                nextion.get_element("cLonEW"),
                nextion.get_element("cSOG"),
                nextion.get_element("cCOG"),
                nextion.get_element("cSat"),
                nextion.get_element("cAlt"),
                {1: "2D", 2: "3D"}.get(nextion.get_element("satfix"), "none"),
            )

        elif part == "1":
            text = (
                "*** Sensoren ***\\r"
                "Temperatur:{}°C\\r"
                "Luftdruck: {} hPa\\r"
                "Druck / 3h:{} hPa\\r"
            ).format(
                nextion.get_element("cTemp"),
                nextion.get_element("cPress"),
                nextion.get_element("cPress3h"),
            )

        elif part == "2":
            text = ("*** SD Karte ***\\rFree:      {} MB\\r").format(
                nextion.get_element("SDCfree")
            )

        else:
            text = "read data..."

        nextion.set_element("p2txt", text, True)

    elif page == "3":
        nextion.refresh_element("cPress")
        nextion.refresh_element("cPress3h")
        nextion.refresh_element("nTemp")


def update(nextion, led):
    page, part = nextion.update()
    # print("page-part", page, part)
    if page is not "0":
        toggle_led(led)
        refresh_page_data(nextion, page, part)


def update_climate_graph(nextion, pressure, temperature):
    # graph height = 250 px
    value = int((float(pressure) - 950) * 2.0)
    nextion.set_element("sys0", value, True)

    value = int((float(temperature) * 6.25))
    nextion.set_element("sys1", value, True)
    print("ClimateGraph updated")
