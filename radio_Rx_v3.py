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

# Image sizing and drawing
img_width = 1
img_height = 1
img_x = 0
img_y = 0
img = Image.new('RGB', (img_width, img_height))
drawer = ImageDraw.Draw(img)

# Correct and incorrect reply packet
reply_packet = bytearray([90,230,17])
wrong_packet = bytearray([])

# Coverting image to array file
img_array = bytearray()
byteImgIO = io.BytesIO()

# Counters
image_counter = 1

# Functions

# Checks received packet for errors using CRC
def packet_handler(packet):
    correct_packet = False
    if packet is None:
        print("- Waiting for Packages -")
    else:
        # Receiving packages
        print("Something has been picked up...")
        if ((packet % CRC_modulo) == 0):
            print("Packet is valid. Continuing file transfer...")
            correct_packet = True
        else:
            print("Error or different signal received. Waiting..."")
    return correct_packet

# Breaks down received packet and adds message pixels to received pixels
def interpret_message(msg, received_pixels):
    is_end = False
    inter_counter = 1
    if (msg[0] == ):
        print("Starting Packet.")
        # Cannot extend from an empty list, so have to initialize instead
        received_pixels = msg[1]
        inter_counter = 2
    elif (msg[0] == ):
        print("Final Packet")
        is_end = True
    else:
        received_pixels = received_pixels
    received_pixels.extend(msg[inter_counter:-1])
    return (is_end, received_pixels)

# Draws image from pixel list and then saves it
# Inspired by javl's slowimage_sender.py
# Need to continue this function
def image_drawer(,image_counter):

    img_bytes = bytes(img_array)
    byteImgIO = io.BytesIO(img_bytes)
    byteImgIO.seek(0)
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    img = Image.open(byteImgIO)
    # Use os.path absolute here instead
    img.save('/home/pi/Desktop/images_received/Target_' + str(image_counter) + '.png')
    print('Image Saved!')
    image_counter += 1
    stage = 1

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
            if packet_handler:
                print("Packet received. RSSI is: " + str(rfm9x.rssi) + ' dbm')
                print("Packet number: " + str(packet_counter))
                is_end, rx_pixels = interpret_message(packet, rx_pixels)
                rfm9x.send(reply_packet)
                if is_end:
                    print("All packages received!")
                    packet = None
                    packet = rfm9x.receive(5.0)
                    # Need to add image width receiving
                    break
                else:
                    packet_counter += 1
            else:
                print("- Waiting for Message -")


# Main function only starts when program is run directly
if __name__ == '__main__':
    main()
