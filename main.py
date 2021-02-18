from vemulator.configuration.config import EmulatorConfig
from vemulator.emulator.emulator import Emulator
from vemulator.input.serialinput import SerialInput
from vemulator.output.standardoutput import StandardOutput
from vemulator.util import log

log.set_stdout_logging(True)
logger = log.init_logger(__name__)

file = 'configs/mppt_text.yaml'  # Config file to be used
input = SerialInput('/dev/ttyUSB0')
# output = SerialOutput('/dev/ttyUSB0')
output = StandardOutput()


def main():
    """
    Run the main emulator program
    """
    config = EmulatorConfig()

    ascii_art()
    logger.info('Started')
    logger.info('Parsing config')
    config.set_config_file(file)
    config.set_input(input)
    config.set_output(output)
    config.set_delay(2)
    config.set_stop_condition('none')
    config.set_bit_error_rate(0.04)
    config.set_timed(False)
    logger.debug(f'Config parsed, fields: {config.get_fields()}')
    logger.info('Creating generators.')
    config.create_scenarios()
    logger.info('Generators created')

    logger.info('Emulation phase')
    emulator = Emulator(config)
    emulator.run()
    logger.info('Finished')


def ascii_art():
    """
    Print 'VEMULATE' as ASCII art
    """
    logger.info('\n'
                '  __      ________ __  __ _    _ _            _______ ______  \n'
                '  \\ \\    / /  ____|  \\/  | |  | | |        /\\|__   __|  ____| \n'
                '   \\ \\  / /| |__  | \\  / | |  | | |       /  \\  | |  | |__    \n'
                '    \\ \\/ / |  __| | |\\/| | |  | | |      / /\\ \\ | |  |  __|   \n'
                '     \\  /  | |____| |  | | |__| | |____ / ____ \\| |  | |____  \n'
                '      \\/   |______|_|  |_|\\____/|______/_/    \\_\\_|  |______|\n'
                )


if __name__ == '__main__':
    main()
