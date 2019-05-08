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

# Correct and incorrect reply packet
reply_packet = bytearray([90,230,17])
wrong_packet = bytearray([])

# Coverting image to array file
img_array = bytearray()
byteImgIO = io.BytesIO()

# Counters
image_counter = 1

# FSM for receiving packages
print("Program Start")
stage = 1
while True:
    print("Ready to receive image...")
    packet_counter = 1
    while (stage == 1):
        packet = None
        packet = rfm9x.receive(5.0)
        if packet is None:
            print('- Waiting for Packages -')
        else:
            # Receiving packages
            print("Something has been picked up...")
            if (packet == start_of_stream):
                rfm9x.send(packet_sent)
                print("Starting Image Transfer!")
                stage = 2
    while (stage == 2):
        # Check for package
        packet = None
        packet = rfm9x.receive(5.0)
        if packet is not None:
        # Receiving package and save it to array variable
            print("Packet received. RSSI is: " + str(rfm9x.rssi) + ' dbm')
            print("Packet number: " + str(packet_counter))
            packet_counter += 1
            rfm9x.send(packet_sent)
            img_array = packet
            stage = 3
    while (stage == 3):
        packet = None
        packet = rfm9x.receive(5.0)
        if packet is not None:
        #all packages received
            if (packet == end_of_stream):
            # Save image into png file and wait for next package
                rfm9x.send(packet_sent)
                print("All packages received!")
                img_bytes = bytes(img_array)
                byteImgIO = io.BytesIO(img_bytes)
                byteImgIO.seek(0)
                ImageFile.LOAD_TRUNCATED_IMAGES = True
                img = Image.open(byteImgIO)
                img.save('/home/pi/Desktop/images_received/Target_' + str(image_counter) + '.png')
                print('Image Saved!')
                image_counter += 1
                stage = 1
            else:
                print("Packet received. RSSI is: " + str(rfm9x.rssi) + ' dbm')
                print("Packet number: " + str(packet_counter))
                img_array.extend(packet)
                packet_counter += 1
                rfm9x.send(packet_sent)
