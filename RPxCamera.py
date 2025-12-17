#!/usr/bin/env python

import socket
import time
import picamera

def RPxLog(severity, message):
	print time.time(), severity, message

def RPxErrLog(message):
	RPxLog("E", message)

def RPxInfoLog(message):
	RPxLog("I", message)

def RPxDevLog(message):
	RPxLog("D", message)


RPxInfoLog("RPxCamera initializing")


with picamera.PiCamera() as camera:
    camera.resolution = (1920, 1080)
    camera.framerate = 24

    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)

    # Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('wb')
    try:
        camera.start_recording(connection, format='h264')
        camera.wait_recording(60)
        camera.stop_recording()
    finally:
        connection.close()
        server_socket.close()



#  vlc tcp/h264://my_pi_address:8000/