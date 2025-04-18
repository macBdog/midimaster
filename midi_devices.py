import time
import mido
import numpy.random as rng

class MidiDevices:
    """ Manager for midi device names and message routing.
    """
    def __init__(self):
        self._input_messages: list[mido.Message] = []
        self._output_messages: list[mido.Message] = []
        self._input_port = None
        self._output_port = None
        self._io_thread = None
        self.input_devices = mido.get_input_names()
        self.output_devices = mido.get_output_names()
        self.input_device_name = None
        self.output_device_name = None


    def output_test(self):
        note_val = rng.randint(32, 64)
        new_note_on = mido.Message("note_on")
        new_note_on.note = note_val
        new_note_on.velocity = 100
        self.output(new_note_on)

        time.sleep(0.075)

        note_off = mido.Message("note_off")
        note_off.note = note_val
        self.output(new_note_on)


    def refresh_io(self):
        self._reconnect()


    def _reconnect(self):
        self.close_input()
        self.close_output()
        time.sleep(1.0)
        self.open_input(self.input_device_name)
        self.open_output(self.output_device_name)


    def open_input(self, input_name:str):
        if self._input_port is None:
            self.input_device_name = input_name
            if input_name not in self.input_devices:
                input_name = self.input_devices[0]

            try:
                self._input_port = mido.open_input(input_name)
                print(f"Opened MIDI input device with name {self.input_device_name}.")
            except Exception as excpt:
                print(f"Could not open MIDI input port: {input_name} with exception {excpt}.")


    def open_output(self, output_name:str):
        if self._output_port is None:
            self.output_device_name = output_name
            if output_name not in self.output_devices:
                output_name = self.output_devices[0]

            try:
                self._output_port = mido.open_output(output_name)
                print(f"Opened MIDI output device with name {self.output_device_name}.")
            except Exception as excpt:
                print(f"Could not open MIDI ouput port: {output_name} with exception {excpt}.")


    def open_input_default(self):
        try:
            self._input_port = mido.open_input()
            self.input_device_name = self._input_port.name
            print(f"Opened MIDI input device with name {self.input_device_name}.")
        except Exception as excpt:
            print(f"Could not open default MIDI input port with exception {excpt}.")


    def open_output_default(self):
        try:
            self._output_port = mido.open_output()
            self.output_device_name = self._output_port.name
            print(f"Opened MIDI output device with name {self.output_device_name}.")
        except Exception as excpt:
            print("Could not open default MIDI output port with exception {excpt}.")


    def output(self, message):
        self._output_messages.append(message)


    def get_output_messages(self):
        return self._output_messages


    def input(self, message):
        self._input_messages.append(message)


    def get_input_messages(self):
        return self._input_messages


    def input_flush(self):
        self._input_messages = []


    def update(self):
        if self.input_device_name:
            for message in self._input_port.iter_pending():
                self._input_messages.append(message)

        if self.output_device_name:
            for message in self._output_messages:
                self._output_port.send(message)
            self._output_messages = []


    def close_input(self):
        if self._input_port is not None:
            self._input_port.close()
            if not self._input_port.closed:
                print ("Unable to close input MIDI port {0}.".format(self.input_device_name))
            self._input_port = None


    def close_output(self):
        if self._output_port is not None:
            self._output_port.close()
            if not self._output_port.closed:
                print("Unable to close output MIDI port {0}.".format(self.output_device_name))
            self._output_port = None


    def end(self):
        self.close_output()
        self.close_input()
