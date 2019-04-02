[![Build Status](https://travis-ci.org/autorope/donkeypart_bluetooth_game_controller.svg?branch=master)](https://travis-ci.org/autorope/donkeypart_bluetooth_game_controller)

# Bluetooth Game Controller
This is a library to connect a [Wii-U](https://www.amazon.com/gp/product/B01GJBUNTG/ref=as_li_ss_tl?ie=UTF8&psc=1&linkCode=ll1&tag=donkeycar-20&linkId=a7fc2ff3e6489b9e6dd267a7f8b2ff19&language=en_US)
 (and possibly others) Bluetooth game controller to your Donkeycar.
 
 >> See the bottom of the page for tested controllers and brands. Beware of knockoffs!



## Install
Install the library.
```bash
git clone https://github.com/autorope/donkeypart_bluetooth_game_controller.git
pip install -e ./donkeypart_bluetooth_game_controller
```


## Connect your bluetooth controller to the raspberry pi.
1. Start the bluetooth bash tool on your raspberry pi.
```bash
sudo bluetoothctl
power on
scan on
```

2. Turn on your controller in scan mode and look for your controllers name in the bluetoothctl scan results.  This is done by turning over the controller and pushing the sync button until the 4 blue buttons blink
3. Connect to your controller using its id (my controller id is `8C:CD:E8:AB:32:DE`) once you've found it's id. You may have to run these commands several times.
```bash
pair 8C:CD:E8:AB:32:DE
connect 8C:CD:E8:AB:32:DE
trust 8C:CD:E8:AB:32:DE
```
4. Now your controller should show that your controller is connected - the 4 blinking lights turns to one solid light.

5. Run the part script to see if it works. You should see all the button values printed as you press them. Like this.
```bash
python ./donkeypart_bluetooth_game_controller/donkeypart_bluetooth_game_controller/part.py


LEFT_STICK_Y 0.00234375
LEFT_STICK_Y 0.0015625
LEFT_STICK_Y 0.00078125
A 1
A 0
Y 1
Y 0
X 1
X 0
```


6. Assuming you can see the button outputs, you can now plug this in as your Donkeycar controller in
the manage.py script...
```python
from donkeypart_bluetooth_game_controller import BluetoothGameController

# then replace your current controller with...
ctl = BluetoothGameController()

```


## Button and stick functionality

* Left stick
    * Forward / backward: Throttle
    * Right / left: Steering

* Control pad (cross)
    * Forward / backward: Throttle scale
    * Right / left: Steering scale

* X: Start recording
* Y: Stop recording
* A: Toggle autonomous driving modes
* B: Manual driving mode

The circular region of the left stick is mapped to a square region, like on a RC remote controller.  This means for the circle of extreme stick deflections:

* The 45 degree positions are mapped to full throttle, full steering deflection.
* The arcs from horizontal to 45 degrees are mapped to full steering (and variable throttle).
* The arcs from forward to 45 degrees are mapped to full throttle (and variable steering).


# Add a new type of Bluetooth controller.
If you don't have a different type of controller these same instructions should work but the button mappings will be different.

1. Use the this same script to show the live output of your controller...
```bash
python ./donkeypart_bluetooth_game_controller/donkeyblue/part.py log
```

2. Copy the [WiiU config](https://github.com/autorope/donkeypart_bluetooth_game_controller/blob/master/donkeyblue/part.py#L86) file and update it with your controllers values.

3. Now you can use your game controller with these new button mappings like this:
```python
from donkeypart_bluetooth_game_controller import BluetoothGameController
ctl = BluetoothGameController(config=/path/to/your/config/file)
```
4. Make a pull request with your button mappings so other people can use it.


# Tested Controllers

## Works
* Wii U Pro Controller by Nintendo


## Kind of Works (Not Recommended)
* Wii U Pro Controller by SIBIONO  - This controller seems laggy give the refresh rate from the controller is half of what better controllers give. 



## Test a New Controller
Run the profile script to see the number of events per second you receive from the controller. Then make a pull request 
to update this document to help others.
```
python ./donkeypart_bluetooth_game_controller/donkeyblue/part.py log
```
