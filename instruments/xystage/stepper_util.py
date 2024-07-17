import serial
import serial.tools.list_ports
from time import sleep
import logging
import os
import yaml

class Stepper:
    def __init__(self):
        """ 
        Controls the stepper motor over serial to an Arduino.
        Examples:
        stepper = Stepper()
        stepper.gohome()
        stepper.moveto(5) # moves x by 5
        stepper.moveto(x_pos=6) # moves x by 6
        stepper.moveto(y_pos=14.23) # moves y by 14.23
        stepper.moveto(3, 4) # moves x by 3 and y by 4
        """
        cur_dir = os.path.dirname(os.path.abspath(__file__))

        self._constants_path = os.path.join(cur_dir, 'hardware_constants.yaml')
        with open(self._constants_path, 'r') as file:
            self._constants = yaml.safe_load(file)

        logging.basicConfig(
            filename = os.path.join(cur_dir, 'XYpy.log'),
            level = logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info('class loaded')

        self.polling_delay = self._constants['stepper']['polling_delay']  # Delay between receiving input from Arduino over Serial and when Python is ready to receive data 
        self.current_x = None
        self.current_y = None

        self.PWM = self._constants['stepper']['pwm'] # duration of the pulses in the PWM signal
        self.PPR = self._constants['stepper']['ppr']  # Pulses per revolution
        self.mm_per_rev = self._constants['stepper']['mm_per_rev']  # Millimeters per revolution

        # self.find_arduino()

        # if self.arduino is None:
        #     logging.error("Aruino not found at any serial port.")
        #     raise RuntimeError("Arduino not found. Please check connection.")
        
    def find_arduino(self):
        """ Find and connect to the Arduino """
        self.arduino = None
        arduino_ports = serial.tools.list_ports.comports()
        for port in arduino_ports:
            if port.pid == self._constants['pid']['arduino'] and port.vid == self._constants['vid']['arduino']:
                self.arduino = serial.Serial(port=port.name, baudrate=self._constants['stepper']['baudrate'], timeout=1)
                logging.info("Arduino Connected")
                print(f"Connected to Arduino at Port {port.name}")
            else:
                pass
    
    def disconnect(self):
        """ Disconnect from the Arduino """
        try:
            self.arduino.close()
            logging.info("Port closed successfully")
        except Exception as e:
            print(f"Failed to close port: {e}")
            logging.error("Failed to close port", exc_info=True)

    def connect(self):
        """ Connect to the Arduino """
        try:
            self.arduino.open()
            logging.info("Port opened successfully")
        except Exception as e:
            print(f"Failed to open port: {e}")
            logging.error("Failed to open port", exc_info=True)

    def gohome(self):
        """ Send 'HOME' command to the Arduino """
        self.arduino.reset_output_buffer()
        self.arduino.reset_input_buffer()
        sleep(self.polling_delay)

        try:
            self.arduino.write("HOME".encode())
            logging.info("Going HOME")
        except Exception as e:
            logging.error("Failed to send 'HOME' command", exc_info=True)

        while self.arduino.in_waiting == 0:
            pass        

        sleep(self.polling_delay)
        num = self.arduino.in_waiting
        string = self.arduino.read(num).strip().decode('utf-8')
        print(f'Stage has been {string}ed')

        self.current_x = 0
        self.current_y = 0

        self.arduino.reset_input_buffer()
        self.arduino.reset_output_buffer()


    def moveto(self, x_pos, y_pos):
        """
        Move to specified x_pos and/or y_pos coordinates.
        If x_pos or y_pos is not specified, current_x or current_y is used respectively.
        """

        try:
            self.arduino.reset_output_buffer()
            self.arduino.reset_input_buffer()

            if self.current_x is None or self.current_y is None:
                logging.error('Please home stage before taking a scan.')
                return

            command, nPulsesX, nPulsesY = self.format_xy(x_pos, y_pos)

            try:
                self.arduino.write(command.encode())
            except Exception as e:
                logging.error(f'Failed to write command to Arduino: {e}')
                return

            # Calculate sleep time based on pulses and PWM
            sleep_time = 1e-6 * (abs(nPulsesX + nPulsesY)) * self.PWM * 2
            sleep(sleep_time)

            # Wait for Arduino response
            while self.arduino.in_waiting == 0:
                pass

            sleep(self.polling_delay)
            
            num = self.arduino.in_waiting

            try:
                response = self.arduino.read(num).strip().decode('utf-8')
            except Exception as e:
                logging.error(f'Failed to read response from Arduino: {e}')
                return

            response_list = response.split('\r\n')

            # Update current_x and current_y based on the movement
            self.current_x = self.current_x + (-1 * nPulsesX * (1 / self.PPR) * self.mm_per_rev)
            self.current_y = self.current_y + (-1 * nPulsesY * (1 / self.PPR) * self.mm_per_rev)

            logging.info(f'(X,Y)={self.current_x},{self.current_y}')

        except Exception as e:
            logging.error(f'An error occurred during movement: {e}')

        finally:
            try:
                self.arduino.reset_input_buffer()
                self.arduino.reset_output_buffer()
            except Exception as e:
                logging.error(f'Failed to reset Arduino buffers: {e}')


    def format_xy(self, posX, posY):
        """
        Format the x and y positions into a command string and calculate number of pulses.
        """
        # Convert the distance to number of turns
        nTurnsX = (self.current_x - posX) / self.mm_per_rev
        nTurnsY = (self.current_y - posY) / self.mm_per_rev
        
        # Convert number of turns to number of pulses, an integer
        nPulsesX = abs(int(nTurnsX * self.PPR))
        nPulsesY = abs(int(nTurnsY * self.PPR))
        
        # Calculate revolutions and remainder pulses
        x_revs = nPulsesX // self.PPR
        x_mod = nPulsesX % self.PPR

        y_revs = nPulsesY // self.PPR
        y_mod = nPulsesY % self.PPR

        # Adjust for direction
        if nTurnsX <= 0:
            x_mod *= -1
            x_revs *= -1
            nPulsesX *= -1
        if nTurnsY < 0:
            y_mod *= -1
            y_revs *= -1
            nPulsesY *= -1

        return f"{x_revs},{x_mod} {y_revs},{y_mod}", nPulsesX, nPulsesY
