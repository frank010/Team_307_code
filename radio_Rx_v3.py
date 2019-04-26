"""

Team 307
Francisco Silva
Matthew Roberts
4/26/2019
RadioRx
This file manages the Tx for the communication system

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

# Start and end of stream for packages
start_of_stream = b'\x01\x02\x03\x04\x05'
end_of_stream = b'\x05\x04\x03\x02\x01'
packet_sent = bytearray([90,230,17])

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
