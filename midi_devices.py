import time
from threading import Thread
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
        self.io_thread = None


    def output_test(self):
        if self.io_thread is None:
            self.io_thread = Thread(target=self._create_test_output)
            self.io_thread.daemon = False
            self.io_thread.start()


    def _create_test_output(self):
        note_on = mido.Message("note_on")
        note_on.note = 60
        note_on.velocity = 100
        self.output_messages.append(note_on)
        
        time.sleep(2.0)

        note_off = mido.Message("note_off")
        note_off.note = 60
        note_off.velocity = 100
        self.output_messages.append(note_off)
        self.io_thread = None


    def refresh_io(self):
        if self.io_thread is None:
            self.io_thread = Thread(target=self._reconnect)
            self.io_thread.daemon = False
            self.io_thread.start()


    def _reconnect(self):
        self.close_input()
        self.close_output()
        time.sleep(1.0)
        self.open_input(self.input_device_name)
        self.open_output(self.output_device_name)


    def open_input(self, input_name:str):
        if self.input_port is None:
            self.input_device_name = input_name
            if input_name in self.input_devices:
                try:
                    self.input_port = mido.open_input(input_name)
                    print(f"Opened MIDI input device with name {self.input_device_name}.")
                except Exception as excpt:
                    print(f"Could not open MIDI input port: {input_name}")
                    print(excpt)


    def open_output(self, output_name:str):
        if self.output_port is None:
            self.output_device_name = output_name
            if output_name in self.output_devices:
                try:
                    self.output_port = mido.open_output(output_name)
                    print(f"Opened MIDI output device with name {self.output_device_name}.")
                except Exception as excpt:
                    print(f"Could not open MIDI ouput port: {output_name}")
                    print(excpt)


    def open_input_default(self):
        try:
            self.input_port = mido.open_input()
            self.input_device_name = self.input_port.name
            print(f"Opened MIDI input device with name {self.input_device_name}.")
        except Exception as excpt:
            print(f"Could not open default MIDI input port.")
            print(excpt)


    def open_output_default(self):
        try:
            self.output_port = mido.open_output()
            self.output_device_name = self.output_port.name
            print(f"Opened MIDI output device with name {self.output_device_name}.")
        except Exception as excpt:
            print("Could not open default MIDI output port.")
            print(excpt)


    def update(self):
        if self.input_device_name:
            for message in self.input_port.iter_pending():
                self.input_messages.append(message)

        if self.output_device_name:
            for message in self.output_messages:               
                self.output_port.send(message)
            self.output_messages = []


    def close_input(self):
        if self.input_port is not None:
            self.input_port.close()
            if not self.input_port.closed:
                print ("Unable to close input MIDI port {0}.".format(self.input_device_name))  


    def close_output(self):
        if self.output_port is not None:
            self.output_port.close()
            if not self.output_port.closed:
                print("Unable to close output MIDI port {0}.".format(self.output_device_name))


    def end(self):
        self.close_output()
        self.close_input()
