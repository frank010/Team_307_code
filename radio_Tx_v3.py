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

# CRC variables
append_CRC = 231

# Counter and index variables
counter = 1
start_index = 0
end_index = 251

# Start and end of stream for packages
start_of_stream = b'\x01\x02\x03\x04\x05'
end_of_stream = b'\x05\x04\x03\x02\x01'
reply_packet = bytearray([90,230,17])

# File stream variables
target_path = os.getcwd() + "/targets/"
target_list = sorted(os.listdir(target_path))
os.path.abspath(target_path + target_list[0])
# Start of Program
print('Program Start')

# Functions
"""

For Polynomial 0xe7, remainer is 0x1cf
append:  1110 0111
modulo:  1 1100 1111
Max message length is: 247

246 bytes left
1 bytes of header information free
245 bytes for pixels
3 bytes per pixels
81.66 pixels per message
~ 950 packages per 320x240 image
To send a 320x240 image in about a minute, you need at least 50 kbps.
Should try to get between 50 to 100 kbps

"""
# Image to pixels and message (built upon javl's slowimage_sender.py functions)
def build_pixels(image_path)
    img_build = Image.open(image_path, mode='r')
    width, height = img_build.size
    pixels = []
    rgb_img_build = img_build.convert('RGB')
    for x_coord in range (0,width)
        for y_coord in range (0,height)
            red, green, blue - rgb_img_build.getpixel((x_coord,y_coord))
            pixels.append(red)
            pixels.append(green)
            pixels.append(blue)
    return pixels

def build_message(pixels, start_index, end_index, part_of_message = 'middle')

    msg = []
    counter_build = start_index
    if (part_of_message == 'start'):
        part_int = 0
    elif (part_of_message == 'end'):
        part_int = 255
    else:
        part_int = 170
    msg.append((part_int).to_bytes(1, byteorder='big'))
    while ((counter_build < end_index) and (counter_build < len(pixels))):
        msg.append(pixels[counter_build])
        counter_build += 1

    msg.append((append_CRC).to_bytes(1, byteorder='big'))
    return msg

# main

while True:

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
