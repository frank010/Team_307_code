"""

Team 307
Francisco Silva
Matthew Roberts
4/26/2019
RadioTx

This program will send an image to the receiver by breaking down images into
pixels, and then sending them in 247 byte packets.
Includes a CRC (Cyclic Redundency Check), and only looks for PNG images.

CRC Information:
Max message length is: 247
Best CRC polynomial from CRC Zoo for a 247 byte long message is 0xe7
For Polynomial 0xe7, remainer is 0x1cf
append before sending: 1110 0111 (0xe7)
modulo when received: 1 1100 1111 (0x1cf)
246 bytes left
1 byte for header information
245 bytes for pixels
3 bytes per pixels
81.66 pixels per message
~ 950 packages per 320x240 image

Notes:
To send a 320x240 image in about a minute, you need at least 50 kbps.
Should try to get between 50 to 100 kbps
Theoretical range at current speed (3 kbps) is ~ 10 kilometers
Realistically, this became between 2-4 kilometers
Raising data rate will lower drone range. May need to buy new antenna or watch
for other sources of noises on drone or interference

"""
# Import Libraries
from PIL import Image, ImageFile
import time
import math
import io
import os
from os.path import isfile, join
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_rfm9x

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

# Correct and incorrect reply packet
reply_packet = bytearray([90,230,17])
wrong_packet = bytearray([])

# Functions

# Image to pixels and message (built upon javl's slowimage_sender.py functions)
def build_pixels(image_path):
    img_build = Image.open(image_path, mode='r')
    width, height = img_build.size
    pixels = []
    num_packages = 0
    rgb_img_build = img_build.convert('RGB')
    for x_coord in range (0,width)
        for y_coord in range (0,height)
            red, green, blue - rgb_img_build.getpixel((x_coord,y_coord))
            pixels.append(red)
            pixels.append(green)
            pixels.append(blue)
    total_bytes = (width * height * 3)
    num_packages = math.floor((total_bytes/245))+1
    return (pixels, num_packages)

# Used to send a large array of pixels through smaller packages
def build_message(pixels, start_index, end_index, part_of_message = 'middle'):
    msg = []
    counter_build = start_index
    # Header information to indicate start, middle, or end of stream
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
    # Insert CRC byte at the end
    msg.append((append_CRC).to_bytes(1, byteorder='big'))
    return msg

# Handles correct and incorrect replies from the receiver
def reply_handler(packet):
    correct_reply = False
    if packet is None:
        print('- Waiting for Packages -')
    else:
        # Receiving packages
        print("Something has been picked up...")
        if (packet == reply_packet):
            print("Reply valid. Continuing file transfer...")
            correct_reply = True
        elif (packet == wrong_packet):
            print('Reply invalid. Error occured at receiver. Waiting...')
        else:
            print('Strange reply received. Waiting...')
    return correct_reply

# Main Function
def main():
    print('Program Start')
    while True:
        # File stream variables
        target_path = os.getcwd() + "/targets/"
        target_list = sorted(os.listdir(target_path))
        # Removes all non PNG images from list of images to send
        for f_stream in target_list:
            if (f_stream.endswith(".png") == False):
                print(f_stream)
                target_list.remove(f_stream)
        print(target_list)
        # Waits till there is a PNG image to send
        if (len(target_list) != 0):
            # Finds an image and grabs an array of its pixels
            img_path = os.path.abspath(target_path + target_list[0])
            img_pixels, num_packages = build_pixels(img_path)

            # Print Image Info
            print('Image grabbed. Preparing to send file...')
            print('The number of packages is: ' + str(num_packages))

            # Start the send process (251 bytes per package)
            stage = 1
            while True:
                while (stage == 1):
                    # Builds a packet with start header
                    msg = build_message(pixels, start_index, end_index, 'start')
                    rfm9x.send(msg)
                    current_packet = str(counter) + '/' + str(num_packages)
                    print("Packet sent: " + current_packet)
                    packet = rfm9x.receive(5.0)
                    if reply_handler(packet):
                        # Updates variables
                        counter += 1
                        start_index += 251
                        end_index += 251
                        stage = 2
                    else:
                        stage = 1
                    time.sleep(1)
                while (stage == 2):
                    while counter < (num_packages):
                        # Builds a packet with middle header
                        msg = build_message(pixels, start_index, end_index)
                        rfm9x.send(msg)
                        current_packet = str(counter) + '/' + str(num_packages)
                        print("Packet sent: " + current_packet)
                        packet = rfm9x.receive(5.0)
                        if reply_handler(packet):
                            # Updates variables
                            counter += 1
                            start_index += 251
                            end_index += 251
                        else:
                            stage = 2
                        time.sleep(1)
                    stage = 3
                while (stage == 3):
                    # Sends last packet
                    msg = build_message(pixels, start_index, end_index, 'end')
                    rfm9x.send(msg)
                    current_packet = str(counter) + '/' + str(num_packages)
                    print("Packet sent: " + current_packet)
                    packet = rfm9x.receive(5.0)
                    if reply_handler(packet):
                        # Reset variables for next image
                        counter = 1
                        start_index = 0
                        end_index = 251
                        print('Image sent')
                        print('Moving to next Image...')
                        time.sleep(3)
                        stage = 1
                        break
                    else:
                        stage = 3
                    time.sleep(1)
        else:
            print('Waiting for more images...')
            time.sleep(1)

# Main function only starts when program is run directly
if __name__ == '__main__':
    main()
