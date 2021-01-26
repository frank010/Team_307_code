"""

Team 307
Francisco Silva
Matthew Roberts
4/26/2019
RadioRx

This program will receiver an image from the transmitter, by receiving
pixels in 247 byte packages, and then drawing them to rebuild the image.
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
#import libraries
from PIL import Image, ImageFile
import time
import io
import array
import os
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
CRC_modulo = 463

# Image variables
new_img_width = 0
new_img_height = 0

# Correct and incorrect reply packet
reply_packet = bytearray([90,230,17])
wrong_packet = bytearray([49,100,442])

# Counters
image_counter = 1

# Functions

# Checks received packet for errors using CRC
def packet_handler(packet):
    correct_packet = 0
    if packet is None:
        print("- Waiting for Packages -")
    else:
        # Receiving packages
        print("Something has been picked up...")
        if ((packet % CRC_modulo) == 0):
            print("Packet is valid. Continuing file transfer...")
            correct_packet = 1
        else:
            print("Error or different signal received. Waiting..."")
            correct_packet = 2
    return correct_packet

# Breaks down received packet and adds message pixels to received pixels
def interpret_message(msg, received_pixels):
    is_end = False
    counter = 1
    # Checking where the pixels should be on the list
    if (int.from_bytes(msg[0], byteorder='big') == 0):
        print("Starting Packet.")
        # Cannot extend from an empty list, so have to initialize instead
        received_pixels = int.from_bytes(msg[1], byteorder='big')
        counter = 2
    elif (int.from_bytes(msg[0], byteorder='big') == 255):
        print("Final Packet.")
        is_end = True
    else:
        received_pixels = received_pixels
    # Adds all pixels from message to the list
    received_pixels.extend(int.from_bytes(msg[counter:-1], byteorder='big'))
    return (is_end, received_pixels)

# Draws image from pixel list and then saves it
# Inspired by javl's slowimage_sender.py
def image_drawer(pix, new_width, new_height, image_counter):
    # Image sizing and drawing
    x = 0
    y = 0
    img_cnt = 0
    img = Image.new('RGB', (new_width, new_height))
    drawer = ImageDraw.Draw(img)
    # First pixel and initialization
    drawer.point((x,y), fill=(pix[img_cnt],pix[img_cnt+1],pix[img_cnt+2]))
    img_cnt += 3
    # Draws pixels onto canvas
    while ((y <= new_height) and ((img_cnt + 3) < len(pix)):
        if((x + 1) > new_width):
            x = 0
            y += 1
        else:
            x += 1
        drawer.point((x,y), fill=(pix[img_cnt],pix[img_cnt+1],pix[img_cnt+2]))
    # Saves PIL picture as PNG image
    img.save(os.getcwd()  + '/received_targets/' + str(image_counter) + '.png')
    print('Image Saved!')

# Main Function
def main():
    print("Program Start")
    while True:
        print("Ready to receive image...")
        # Initialize variables
        rx_pixels = []
        packet_counter = 1
        receiving_image = True
        # FSM for receiving packages
        while receiving_image:
            packet = None
            packet = rfm9x.receive(5.0)
            if (packet_handler == 1):
                # Print signal strength
                print("Packet received. RSSI is: " + str(rfm9x.rssi) + ' dbm')
                print("Packet number: " + str(packet_counter))
                is_end, rx_pixels = interpret_message(packet, rx_pixels)
                rfm9x.send(reply_packet)
                if is_end:
                    print("All packages received!")
                    # Receiving image width
                    packet = None
                    packet = rfm9x.receive(5.0)
                    img_width = int.from_bytes(packet)
                    rfm9x.send(reply_packet)
                    print("Image width received: " + img_width)
                    # Receiving image height
                    packet = None
                    packet = rfm9x.receive(5.0)
                    img_height = int.from_bytes(packet)
                    rfm9x.send(reply_packet)
                    print("Image height received: " + img_height)
                    # Saving image and resetting variables
                    image_drawer(rx_pixels,img_width,img_height,image_counter)
                    image_counter += 1
                    receiving_image = False
                    break
                else:
                    packet_counter += 1
            elif (packet_handler == 2):
                rfm9x.send(wrong_packet)
                print("- Waiting for Message -")
            else:
                print("- Waiting for Message -")

# Main function only starts when program is run directly
if __name__ == '__main__':
    main()
