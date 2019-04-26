"""
Team 307
Francisco Silva
Matthew Roberts
4/26/2019
RadioRx
This file manages the Rx for the communication system

"""
# Import Libraries
from PIL import Image, ImageFile
import time
import math
import io
import array
import os
from os.path import isfile, join
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_rfm9x
import glob

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Configure LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize the LoRa Radio
try:
    rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
    print('RFM9x: Detected')
except RuntimeError:
    # Thrown on version mismatch
    print('RFM9x: ERROR')

# Configure LoRa parameters
rfm9x.tx_power = 23

# Counter and index variables
counter = 1
start_index = 0
end_index = 251

# Start and end of stream for packages
start_of_stream = b'\x01\x02\x03\x04\x05'
end_of_stream = b'\x05\x04\x03\x02\x01'
reply_packet = bytearray([90,230,17])


# Start of Program
print('Program Start')

while True:
    target_path = os.getcwd() + "/targets/"
    target_list = sorted(os.listdir(target_path))
    for f_stream in target_list:
        if (f_stream.endswith(".png") == False):
            print(f_stream)
            target_list.remove(f_stream)
    print(target_list)
    if (len(target_list) != 0):
        # Configuring the image using PIL
        img = Image.open(os.path.abspath(target_path + target_list[0]), mode='r')
        img_byte_array = io.BytesIO()
        img.save(img_byte_array, 'png')
        img_str = img_byte_array.getvalue()
        num_packages = math.floor((len(img_str)/251))+1
        # Print Image Info
        print(len(img_str))
        print('Image grabbed. Preparing to send...')
        print('Image size: ' + str(len(img_str)))
        print('The number of packages is: ' + str(num_packages))
        print('Image Stream started')
        # Start the send process (251 bytes per package)
        stage = 1
        while True:
            while (stage == 1):
                # Send start package here
                rfm9x.send(start_of_stream)
                packet = rfm9x.receive(1.0)
                if packet is None:
                    print('- Waiting for Packages -')
                else:
                    # Receiving packages
                    print("Something has been picked up...")
                    if (packet == reply_packet):
                        print("Starting Image Transfer!")
                        stage = 2
                    else:
                        print('Reply invalid. Waiting...')
                        time.sleep(1)
            while (stage == 2):
                while counter < (num_packages):
                    msg = img_str[start_index:end_index]
                    #print(msg)
                    rfm9x.send(msg)
                    print("Package sent: " + str(counter) + '/' + str(num_packages))
                    packet = rfm9x.receive(1.0)
                    if packet is None:
                        print('- Waiting for Packages -')
                    else:
                        # Receiving packages
                        # print("Something has been picked up...")
                        if (packet == reply_packet):
                            print('Reply received. Moving to next package...')
                            #print(str(counter))
                            counter += 1
                            start_index += 251
                            end_index += 251
                            time.sleep(0.1)
                        else:
                            print('Reply invalid. Waiting...')
                            time.sleep(1)
                stage = 3
            # Send last package that has < 254 bytes
            while (stage == 3):
                print('Last package!')
                msg = img_str[start_index:]
                rfm9x.send(msg)
                print("Last package sent.")
                if (packet == reply_packet):
                    print('Last reply received. Sending end of stream...')
                    stage = 4
                else:
                    print('Reply invalid. Waiting...')
                    time.sleep(1)
            # Signal end of stream the receiver
            while (stage == 4):
                time.sleep(1)
                rfm9x.send(end_of_stream)
                packet = rfm9x.receive(5.0)
                if packet is None:
                    print('- Waiting for Packages -')
                else:
                    # Receiving packages
                    print("Something has been picked up...")
                    if (packet == reply_packet):
                        # Reset variables for next image
                        counter = 1
                        start_index = 0
                        end_index = 251
                        stage = 1
                        break
                    else:
                        print('Reply invalid. Waiting...')
                        time.sleep(1)
            print('Image Sent')
            print('Moving to next Image...')
            time.sleep(5)
    else:
        print('Waiting for more images...')
        time.sleep(1)
