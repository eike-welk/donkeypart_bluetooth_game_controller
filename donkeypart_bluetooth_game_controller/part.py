# Controller part for the Donkeycar, that controls the car with a Bluetooth
# game controller. It replaces the Web-Controller.
# 
# The part can in principle work with any Bluetooth game controller, however 
# there is only a configuration file for the "Wii U Pro Controller".

import os
import time
from itertools import cycle
from math import sqrt
import argparse
import evdev
from evdev import ecodes
import yaml

class BluetoothDevice:
    """
    Base class for Bluetooth input devices.

    Can search for Bluetooth devices that have a certain name.
    The matching device is put into `self.device`
    """
    def __init__(self, verbose=False):
        self.device = None
        self.verbose = verbose

    def get_input_device(self, path):
        return evdev.InputDevice(path)

    def find_input_device(self, search_term):
        """
        Return the input device if there is only one that matches the search term.
        """
        all_devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        likely_devices = []
        for device in all_devices:
            if search_term.lower() in device.name.lower():
                likely_devices.append(device)

        if self.verbose:
            msg = 'Found input devices: \n' \
                + ', '.join([device.name for device in all_devices]) \
                + '\n'
            print(msg)

        if len(likely_devices) == 1:
            # correct device was likely found
            return likely_devices[0]

        if len(likely_devices) >= 2:
            msg = 'Found multiple input devices with matching names: \n' \
                + ', '.join([device.name for device in likely_devices]) \
                + '\n\n' \
                + 'Please specify a unique name for the desired device.'
            print(msg)
            raise ValueError(msg)

    def load_device(self, search_term):
        """
        Try to load the device until one that matches the search term exists.
        """
        device = None
        while device is None:
            device = self.find_input_device(search_term)
            if device is None:
                print("Device matching '{}' couldn't be found. "
                      "Trying again in 3 seconds."
                      .format(search_term))
                time.sleep(3)
        self.device = device


class BluetoothGameController(BluetoothDevice):
    """
    Controller part for the Donkeycar, that controls the car with a Bluetooth
    game controller. It replaces the Web-Controller.
    """

    def __init__(self, event_input_device=None, config_path=None, 
                 device_search_term=None, verbose=False):
        super().__init__(verbose)
        self.running = False

        self.state = {}
        self.angle = 0.0
        self.throttle = 0.0

        # For mapping the stick's circular region to a square.
        self.u = 0
        self.v = 0

        self.angle_scale = 1.0
        self.angle_scale_increment = .05
        self.throttle_scale = 1.0
        self.throttle_scale_increment = .05
        self.y_axis_direction = -1  # pushing stick forward gives negative values

        self.drive_mode_toggle = cycle(['user', 'local_angle', 'local'])
        self.drive_mode_autonomous_toggle = cycle(['local_angle', 'local'])
        self.drive_mode = next(self.drive_mode_toggle) # 'user'

        self.recording_toggle = cycle([True, False])
        self.recording = next(self.recording_toggle) # True

        if config_path is None:
            config_path = self._get_default_config_path()
        self.config = self._load_config(config_path)

        self.btn_map = self.config.get('button_map')
        self.joystick_max_value = self.config.get('joystick_max_value', 1280)

        # search term used to find the event stream input (/dev/input/...)
        self.device_search_term = device_search_term or self.config.get('device_search_term', 1280)

        if event_input_device is None:
            self.load_device(self.device_search_term)
            print(self.device)
        else:
            self.device = event_input_device

#        self.func_map = {
#            'RIGHT_STICK_X': self.update_angle,
#            'LEFT_STICK_Y': self.update_throttle,
#            'B': self.toggle_recording,
#            'A': self.toggle_drive_mode,
#            'PAD_UP': self.increment_throttle_scale,
#            'PAD_DOWN': self.decrement_throttle_scale,
#        }

        self.func_map = {
            'LEFT_STICK_X': self.update_stick_x_map,
            'LEFT_STICK_Y': self.update_stick_y_map,
            'X': self.start_recording,
            'Y': self.stop_recording,
            'B': self.set_drive_mode_manual,
            'A': self.toggle_drive_mode_autonomous,
            'PAD_RIGHT': self.increment_angle_scale,
            'PAD_LEFT': self.decrement_angle_scale,
            'PAD_UP': self.increment_throttle_scale,
            'PAD_DOWN': self.decrement_throttle_scale,
        }

    def _get_default_config_path(self):
        return os.path.join(os.path.dirname(__file__), 'wiiu_config.yml')

    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            config = yaml.load(f)
        return config

    def read_loop(self):
        """
        Read input, map events to button names and scale joystic values to between 1 and 0.
        """
        try:
            event = next(self.device.read_loop())
            btn = self.btn_map.get(event.code)
            val = event.value
            if btn == None and self.verbose:
                print('Unknown event: {}, value: {}'
                        .format(event.code, event.value))
            if event.type == ecodes.EV_ABS:
                val = val / float(self.joystick_max_value)
            return btn, val
        except OSError as e:
            print('OSError: Likely lost connection with controller. Trying to reconnect now. Error: {}'.format(e))
            time.sleep(.1)
            self.load_device(self.device_search_term)
            return None, None


    def update_state_from_loop(self):
        btn, val = self.read_loop()

        # update state
        self.state[btn] = val

        # run_functions
        func = self.func_map.get(btn)
        if func is not None:
            func(val)

        if self.verbose == True:
            print("button: {}, value:{}".format(btn, val))

    def update(self):
        while True:
            self.update_state_from_loop()

    def run(self):
        self.update_state_from_loop()
        return self.angle, self.throttle, self.drive_mode, self.recording

    def run_threaded(self, img_arr=None):
        return self.angle, self.throttle, self.drive_mode, self.recording

    def shutdown(self):
        self.running = False
        time.sleep(0.1)

    def profile(self):
        msg = """
        Starting to measure the events per second. Move both joysticks around as fast as you can. 
        Every 1000 events you'll see how many events are being recieved per second. After 10,000 records
        you'll see a score for the controller. 
        """
        print(msg)
        event_total = 0
        start_time = time.time()
        results = []
        while True:
            self.read_loop()
            event_total += 1
            if event_total > 1000:
                end_time = time.time()
                seconds_elapsed = end_time - start_time
                events_per_second = event_total / seconds_elapsed
                results.append(events_per_second)
                print('events per seconds: {}'.format(events_per_second))
                start_time = time.time()
                event_total = 0
                if len(results) > 9:
                    break

        sorted_results = sorted(results)
        best_5_results = sorted_results[5:]
        max = best_5_results[-1]
        average = sum(best_5_results) / len(best_5_results)

        print('RESULTS:')
        print('Events per second. MAX: {}, AVERAGE: {}'.format(max, average))


    def circ_to_square(self, u, v):
        """
        Map a circular region to a square region.

        The formula is taken from:
            http://squircular.blogspot.com/2015/09/mapping-circle-to-square.html
        """
        def max0(x):
            return max(x, 0)

        sqrt2 = sqrt(2)
        x = 0.5 * ( sqrt(max0(2 + 2 * u * sqrt2 + u*u - v*v ))
                  - sqrt(max0(2 - 2 * u * sqrt2 + u*u - v*v )))
        y = 0.5 * ( sqrt(max0(2 + 2 * v * sqrt2 - u*u + v*v ))
                  - sqrt(max0(2 - 2 * v * sqrt2 - u*u + v*v )))
        return x, y

    def update_stick_x_map(self, val):
        """
        React to stick X input event.
        
        Map circular region of the stick to the required square region for
        independent angle and throttle input.
        """
        self.u = val
        x, y = self.circ_to_square(self.u, self.v)
        self.angle = x * self.angle_scale
        self.throttle = y * self.throttle_scale * self.y_axis_direction

    def update_stick_y_map(self, val):
        """
        React to stick Y input event.
        
        Map circular region of the stick to the required square region for
        independent angle and throttle input.
        """
        self.v = val
        x, y = self.circ_to_square(self.u, self.v)
        self.angle = x * self.angle_scale
        self.throttle = y * self.throttle_scale * self.y_axis_direction

    def update_angle(self, val):
        self.angle = val * self.angle_scale
        return

    def update_throttle(self, val):
        self.throttle = val * self.throttle_scale * self.y_axis_direction
        return

    def toggle_recording(self, val):
        if val == 1:
            self.recording = next(self.recording_toggle)
        return

    def start_recording(self, val):
        if val == 1:
            self.recording = True

    def stop_recording(self, val):
        if val == 1:
            self.recording = False

    def toggle_drive_mode(self, val):
        if val == 1:
            self.drive_mode = next(self.drive_mode_toggle)
        return

    def set_drive_mode_manual(self, val):
        if val == 1:
            self.drive_mode = 'user'

    def toggle_drive_mode_autonomous(self, val):
        if val == 1:
            if self.drive_mode == 'user':
                # Let automatic driving always start with 'local_angle'
                self.drive_mode_autonomous_toggle = cycle(['local_angle',
                                                           'local'])
            self.drive_mode = next(self.drive_mode_autonomous_toggle)

    def increment_angle_scale(self, val):
        if val == 1:
            self.angle_scale += self.angle_scale_increment
        return

    def decrement_angle_scale(self, val):
        if val == 1:
            self.angle_scale -= self.angle_scale_increment
        return

    def increment_throttle_scale(self, val):
        if val == 1:
            self.throttle_scale += self.throttle_scale_increment
        return

    def decrement_throttle_scale(self, val):
        if val == 1:
            self.throttle_scale -= self.throttle_scale_increment
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                description='Script to help test and setup your Bluetooth controller.')
    parser.add_argument('command', metavar='command', type=str, 
                        choices=['log', 'profile'],
                        help='Possible commands are: "log", "profile"')
    parser.add_argument('search_term', metavar='search-term', type=str, nargs='?',
                        default='Nintendo',
                        help='A string that can identify the Bluetooth device. '
                             'Default: "Nintendo"')

    args = parser.parse_args()
    #print(args.command)
    #print(args.search_term)

    device_search_term = args.search_term
    if args.command == 'profile':
        ctl = BluetoothGameController(device_search_term=device_search_term)
        ctl.profile()
    elif args.command == 'log':
        ctl = BluetoothGameController(verbose=True, device_search_term=device_search_term)
        ctl.update()

