
"""
# Send values, strings to icrocontroller {set_num, set_txt}
Header  Command         Name        Delimiter   Value       Tail
['@']   [set_num/txt]   ['Name']    ['$']       ['1000']    ['#']

# Request values, strimgs from microcontroller {get_num, get_txt}
Header  Command         Name        Tail
['@']   [get_num/txt]   ['Name']    ['#']

# Request page data bulk refresh {get_page_data}
Header  Command         Page        Part        Tail
['@']   [get_page_data] [0..9-A..Z] [0..9-A..Z] ['#']

# Set / Reset button or action triggers {action_set, action_reset}
Header  Command         Name        Tail
['@']   [action_set]   ['Name']    ['#']
['@']   [action_reset] ['Name']    ['#']
"""

class Nextion:

    GET_PAGE_DATA       = const(0x70) # Zeichen p

    SET_NUM             = const(0x4e) # Zeichen N / Nextion sends value to store
    GET_NUM             = const(0x6e) # Zeichen n
    SET_TXT             = const(0x54) # Zeichen T
    GET_TXT             = const(0x74) # Zeichen t

    ACTION_SET          = const(0x42) # Zeichen B
    ACTION_RESET        = const(0x62) # Zeichen b

    COM_STATE_IDLE      = const(0)
    COM_STATE_READING   = const(1)
    COM_STATE_EXECUTE   = const(2)
    
    COM_HEAD            = const(0x40) # Zeichen @
    COM_DELIMITER       = const(0x24) # Zeichen $
    COM_TAIL            = const(0x23) # Zeichen #

    def __init__(self, uart):
        self._uart = uart
        self._com_state = COM_STATE_IDLE
        self._com_data = []
        self._element_db = {}
        self._sysvars = ["sys0", "sys1", "sys2"]

    def _send(self, buf):
        # send data to Nextion, add end of message tail
        self._uart.write(buf.encode())
        self._uart.write(b'\xff\xff\xff')

    def _c2t(self, data):
        # convert bytearray to string
        data_string = ''.join([chr(b) for b in data])
        return data_string

    def _c2n(self, data):
        # convert bytearray to integer
        data_string = ''.join([chr(b) for b in data])
        return int(data_string)

    def _send_val(self, name, value):
        # prepare data string depending on type
        if isinstance(value, str):
            self._send(name + ".txt=" + '"' + value + '"')
        else:
            if name in self._sysvars:
                self._send(name + "=" + str(value))
            else:
                self._send(name + ".val=" + str(value))

    def add_element(self, name, value):
        # add element to dictionary
        self._element_db[name] = value

    def get_element(self, name):
        # beware, if element is not found, None ist returned
        return self._element_db.get(name)

    def set_element(self, name, value, refresh = False):
        # ignore names not found in dictionary
        if name in self._element_db:
            self._element_db[name] = value
            if refresh:
                self._send_val(name, value)

    def refresh_element(self, name):
        # send element to Nextion
        if name in self._element_db:
            self._send_val(name, self.get_element(name))

    def _execute_request(self, page, part):
        # process incomming command
        command = self._com_data[0]
        if command == GET_PAGE_DATA:
            page = chr(self._com_data[1])
            part = "0"
            if len(self._com_data) == 3:
                part = chr(self._com_data[2])

        elif command in [SET_TXT, SET_NUM]:
            name, delimiter, value = (
                self._com_data[1:].decode("latin-1").partition(COM_DELIMITER)
            )
            if not delimiter:
                raise ValueError(
                    "delimiter {!r} not found in {!r}".format(
                        COM_DELIMITER, self._com_data
                    )
                 )
            self.set_element(name, int(value) if command == SET_NUM else value)
            print("SET_TXT/NUM:", name, value)

        elif command in [GET_TXT, GET_NUM]:
            name = self._c2t(self._com_data[1:])
            self.refresh_element(name)
            print("GET_TXT/NUM:", name)

        elif command == ACTION_SET:
            name = self._c2t(self._com_data[1:])
            self.set_element(name, 1)
            print("ACTION_SET:", name)

        elif command == ACTION_RESET:
            name = self._c2t(self._com_data[1:])
            self.set_element(name, 0)
            print("ACTION_RESET:", name)

        else:
            print("Nextion: unknown request:", self._com_data)

        return page, part

    def update(self):
        page = part = "0"
        while self._uart.in_waiting:
            byte_value = self._uart.read(1)[0]
            if self._com_state == COM_STATE_IDLE:
                if byte_value == COM_HEAD:
                    self._com_data.clear()
                    self._com_state = COM_STATE_READING

            elif self._com_state == COM_STATE_READING:
                if byte_value == COM_TAIL:
                    self._com_state = COM_STATE_EXECUTE
                else:
                    self._com_data.append(byte_value)
            
            # else:
            #     assert False, "unexpeted state {!r}".format(self._com_state)

            if self._com_state == COM_STATE_EXECUTE:
                self._com_state = COM_STATE_IDLE
                if len(self._com_data) > 1:
                    page, part = self._execute_request(page, part)

        return page, part

