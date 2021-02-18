# VEmulator
VEmulator allows the emulation of devices that use the VE.Direct text and/or hex protocol. During the implementation 
of the emulator, the following naming convention has been agreed upon: a VE.Direct text/hex message can have one or more
_fields_ which have a certain _value_. How these values are generated is determined by the _scenarios_ defined for this field.

## Installing
To make sure all the required packages are installed before running the emulator, first run `pip install .`

## Running
To run the emulator two classes are needed. First, an instance of vemulator.configuration.config.EmulatorConfig needs to be created. 
This config instance can then be used to set up the emulator, including what it should use for inputting and outputting hex/text messages, for which classes 
can be found in vemulator.input and vemulator.output
Then, this config needs to be passed to an instance of vemulator.generator.emulator.Emulator which can then be started. An example of this can be seen below:

```python
from vemulator.configuration.config import EmulatorConfig
from vemulator.util import log
from vemulator.emulator.emulator import Emulator
from vemulator.input.serialinput import SerialInput
from vemulator.output.serialoutput import SerialOutput

# By default, errors and other info is logged to config files
# By setting this to true, errors will also be logged to stdout:
log.set_stdout_logging(True)

config = EmulatorConfig()  # Create a new emulator config
config.set_config_file('config.yaml')  # Set a config file
config.set_input(SerialInput('/dev/tty0'))  # Input from which to read hex messages
config.set_output(SerialOutput('/dev/tty0'))  # Output to which hex and text messages should be written
config.set_delay(1)  # Delay between text messages 
config.set_bit_error_rate(0.04)  # Bit error rate 
config.set_bit_error_checksum(True)  # Also add errors to the checksum
config.set_default_seed(10)  # Seed to use by default for RNG
config.create_scenarios()  # Create generators based on the fields in the config file

emulator = Emulator(config)  # Create the emulator using the config
emulator.run()  # Start the emulator

# Other useful functions:
emulator.pause()  # Pause the emulator
emulator.resume()  # Resume the emulator
emulator.stop()  # Stop the emulator
emulator.get_status()  # Get the status of the emulator
emulator.overwrite_text_scenarios('key', [])  # Overwrite the scenarios of a text field that are used for value generation
emulator.overwrite_hex_scenarios('key', [])  # Overwrite the scenarios of a hex field that are used for value generation
```

## Unit tests
To run the unit tests, run `python3 test.py`. If this prints `OK` at the end, all unit tests have completed successfully.
If the unit tests take more than about a second there is probably an infinite loop somewhere in the code where it should not be.

# Directory structure 
```
🗁 configs    # Contains the base yaml configurations for several devices
🗁 protocols  # Contains preset yaml configurations for several fields
🗁 vemulator  # Contains the source code of the emulator
└─ 🗁 configuration  # Contains code related to the configuration of the emulator and the reading of config files
└─ 🗁 events         # Contains code related to the event queue for time based value generation
└─ 🗁 generator      # Contains the emulator itself that handles incoming and outgoing messages
└─ 🗁 input          # Contains code for several input options for reading incoming hex messages
└─ 🗁 output         # Contains code for several output options for writing outgoing hex and text messages
└─ 🗁 scenarios      # Contains code for all the different scenario types 
└─ 🗁 tests          # Contains unit tests for the emulator
└─ 🗁 util           # Contains several utility functions
```

## Configuration
When running the emulator, a configuration should be added. Some example configurations can be found in `/configs`. 
These configs are written in yaml. When the emulator is run, the config file will first be checked for errors and if 
the config is invalid, an error will be written to the error log describing what is wrong.  
When defining fields in a config, one can include predefined fields by using them as so-called presets. 
These preset fields can be found in `/protocols`, where the name of the directory inside `/protocols` is the name of the 
preset, and the name of the yaml files inside those directories (excluding the extension) is the name of the field to include.

Fields can have values of all kinds of types. Some of these types can be found in the presets in the `/protocols` directory. 
Apart from this, the all so-called scenario types can be found in the `/vemulator/scenarios` directory. In these source files,
a usage example is given for each of these scenarios. A list overview of the scenarios, and their purpose, can be found below: 

- `Arithmetic` Calculate a value based on the value of one or more other fields
- `Gradient` Generate values based on a mathematical function of time
- `IntBoundary` Generates numbers within a certain boundary
- `IntChoice` Chooses values from a list of integers
- `IntFixed` A fixed integer value
- `IntRandom` Generates a random integer value
- `IntRange` Generates numbers within a certain range
- `Regex` Generates strings that match a regex
- `Mapping` Similar to choice scenarios but a description of the values can also be provided
- `StringFixed` A fixed string value
- `SelectRandom` Randomly selects one of its child scenarios
- `StringBoundary` Generates strings within a certain length boundary
- `StringChoice` Chooses values from a list of strings
- `StringRandom` Generates a random string value
- `StringUnicode` Generates a random string value that can contain all unicode characters (not necessarily ascii characters)

An example of the structure of a config file can be found here: 

```yaml
device: Device Name # Name of the device that is emulated
name: Test 1 # Name of this configuration
protocol: text_hex # Protocol used in this test, 'text' to only support text protocol, 'text_hex' to support both text and hex protocols, 'hex' to only support hex protocol
version: 0x4147 # Firmware version, optional if not using hex protocol
product_id: 0xA04C # Product ID, optional if not using hex protocol
bootloader: 0x51FA51FA51FA51FA51FA # Payload required to enter boot mode, false by default to disable 'boot' command

preset: vedirect_330 # The preset to use
preset_fields: # These fields are 'imported' from the specified preset
  - v: default # Can be either default, random or fuzzing. With default, the fixed default value of the field will be returned, random will generate random values and fuzzing will generate fuzzing values like boundary values
  - v1: fuzzing
    override: # One can use override to use the field properties of a preset but override certain properties
      values:
        - type: IntRandom
          amount: 8
          min: 0
          max: 10
      invalid: []
  - v2: random
  - h1: default

fields: # Fields for text protocol
  - name: Voltage # Human readable name of the field
    key: V # Key of the field used in the text protocol
    units: mV # Unit of the field
    scale: 0.1 # Scale of the field
    interval: 2 # Default is 1; indicates the interval in seconds between the generation of new values. This property is only used when the emulator is run in timed mode.
    values: # List of scenarios used to generate values for the field
      - type: IntRandom # Scenario type
        amount: 8 # Number of values that are generated using this scenario; can be left out to generate infinite values
        min: 0 # Specific property to IntRandom, see docstrings in the scenarios for more detailed explanation of all the properties
        max: 10
      - type: IntRandom # Once 8 random integers between 0-10 have been generated, the emulator will move to this scenario
        amount: 3
        min: -10
        max: 0
      - type: IntRandom
        amount: 5
        min: 100
        max: 500
      - type: Loop # Loop can be used to generate a sequence of values multiple times
        amount: 1
        values:
          - type: Loop # You can add loops inside loops
            amount: 2
            values:
            - type: IntFixed
              amount: 2
              value: 1
            - type: IntFixed
              amount: 2
              value: 2
          - type: IntFixed
            amount: 2
            value: 3
  - name: Amperage
    key: A
    units: mA
    values:
      - type: IntRandom
        amount: 4
        min: 0
        max: 5
  - name: Test
    key: T
    units: T
    values:
      - type: Arithmetic # Arithemtic can be used to generate values based on the value of other values
        value: V * A * 100 # Any referenced fields used here should be defined above the Arithmetic field
  - name: Auxiliary (starter) voltage
    key: VS
    unit: mV
    values:
      - type: Loop
        amount: 1 # Amount of times to loop, -1 to loop infinitely
        values:
          - type: Gradient
            gradient_type: parabolic
            step_size: 1
            min: 0
            max: 10
          - type: Loop
            amount: 1
            values:
              - type: IntBoundary
                amount: 1
                seed: 0 # You can specify a seed to use a different seed than the global seed for this field
                min: 0
                max: 10

hex_fields: # Fields for hex protocol
  - name: Voltage # A hex field is similar to a text field
    key: 0x1234 # The only difference is that the key is now a hexadecimal value
    unit: mV
    values:
      - type: IntBoundary
        bits: 8 # For hex fields, a bit size needs to be given
        signed: true # An integer can be indicated as signed when using hex
        min: 0x00
        max: 0xFF
        writable: true # false by default, if true, this field is able to be updated using the hex 'set' command
        async_change: true # false by default, send this field as async message when it changes
        async_interval: 5 # false by default, send this field as async message at a set interval in seconds
      - type: IntRandom
        bits: 8
        amount: 0
        min: 0x00
        max: 0xFF
      - type: IntFixed
        bits: 8
        value: 0x0A
      - type: IntChoice
        bits: 8
        choices: [0x00, 0x01, 0x02]
      # And all other fields available in text protocol, fields will be encoded as hex
  - name: VS
    key: 0x1235
    unit: mV
    values:
      - type: IntFixed
        value: 0x0A
        bits: 8
        writable: true
```