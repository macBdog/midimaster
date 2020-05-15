import mido

class MidiDevices:
    """ Manager for midi device names and message routing.
    """
    def __init__(self):
        self.input_devices = mido.get_input_names()
        self.output_devices = mido.get_output_names()
        self.input_device_name = None
        self.output_device_name = None
        self.input_messages = []
        self.output_messages = []
        self.input_port = None
        self.output_port = None

    def open_input(self, input_name):
        if self.input_port is None:
            self.input_device_name = input_name
            if input_name in self.input_devices:
                self.input_port = mido.open_input(input_name)

    def open_output(self, output_name):
        if self.output_port is None:
            self.output_device_name = output_name
            if output_name in self.output_devices:
                self.out_port = mido.open_output(output_name)

    def open_input_default(self):
        if len(self.input_devices) > 0:
            self.open_input(self.input_devices[0])

    def open_output_default(self):
        if len(self.output_devices) > 0:
            self.open_output(self.output_devices[0])

    def update(self):
        if self.input_device_name:
            for message in self.input_port:
                self.input_messages.append(message)

        if self.output_device_name:
            for message in self.output_messages:               
                self.out_port.send(message)
            self.output_messages = []