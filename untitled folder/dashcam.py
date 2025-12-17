import datetime
import RPi.GPIO as GPIO
import time
import os
import subprocess
import gps

def Log(t, s):
	print time.time(),t,s

Log("!", "started dashcam.py")

# Listen on port 2947 (gpsd) of local host
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

# Set mode
GPIO.setmode(GPIO.BOARD)
# Hide warnings
GPIO.setwarnings(False)
# RPi.GPIO version
#print "RPi.GPIO version = %s" % (GPIO.VERSION)
# RPi board revision
#print "RPi board revision = %s" % (GPIO.RPI_REVISION)

# Setup inputs
# Record = Button1 = GPIO15 = Board 10
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Parking = Button2 = GPIO17 = Board 11
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Manual Event = Button3 = GPIO18 = Board 12
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Not used
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Ignition power = Button5 = GPIO22 = Board 15
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Acceleration sensor = Button6 = GPIO23 = Board 16
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Not used 
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Not used 
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Setup outputs & turn all LEDS off
# LED 1 = GPIO2 = Board 3
GPIO.setup(3, GPIO.OUT)
GPIO.output(3, GPIO.LOW)
# LED 2 = GPIO3 = Board 5
GPIO.setup(5, GPIO.OUT)
GPIO.output(5, GPIO.LOW)
# Parked = LED 3 = GPIO4 = Board 7
GPIO.setup(7, GPIO.OUT)
GPIO.output(7, GPIO.LOW)
# Event = LED 4 = GPIO7 = Board 26
GPIO.setup(26, GPIO.OUT)
GPIO.output(26, GPIO.LOW)
# Power = LED 5 = GPIO8 = Board 24
GPIO.setup(24, GPIO.OUT)
GPIO.output(24, GPIO.HIGH)
# Record = LED 6 = GPIO9 = Board 21
GPIO.setup(21, GPIO.OUT)
GPIO.output(21, GPIO.HIGH)
# LED 7 = GPIO10 = Board 19
#GPIO.setup(19, GPIO.OUT)
#GPIO.output(19, GPIO.LOW)
# LED 8 = GPIO11 = Board 23
#GPIO.setup(23, GPIO.OUT)
#GPIO.output(23, GPIO.LOW)

# Intialise dashcam
mode = 'recording'
Log("M", "%s" % mode)
os.system("aplay -q audio/Recording_Started.wav &")

# Record button pressed
def mode_record(channel):
	global mode
	if mode != 'recording':
		mode='recording'
		Log("M", "%s" % mode)
		GPIO.output(21, GPIO.HIGH) # Record
		GPIO.output(7, GPIO.LOW) # Parking
		GPIO.output(26, GPIO.LOW) # Event
		os.system("aplay -q audio/Recording_Mode.wav &")
GPIO.add_event_detect(10, GPIO.FALLING, callback=mode_record, bouncetime=500)

# Parked button pressed
def mode_parked(channel):
	global mode
	if mode != 'parked':
		mode = 'parked'
		Log("M", "%s" % mode)
		GPIO.output(21, GPIO.LOW) # Record
		GPIO.output(7, GPIO.HIGH) # Parking
		GPIO.output(26, GPIO.LOW) # Event
		os.system("aplay -q audio/Parking_Mode.wav &")
GPIO.add_event_detect(11, GPIO.FALLING, callback=mode_parked, bouncetime=500)

# Acceleration sensor event
def acceleration_event(channel):
	Log("=", "acceleration sensor")
	GPIO.output(26, GPIO.HIGH) # Event
	# Set flag to store events
	f = open('dashcam.event', 'w')
	f.write('true\n')
	f.close()
GPIO.add_event_detect(16, GPIO.FALLING, callback=acceleration_event, bouncetime=500)

# Ignition cut event
def ignition_cut(channel):
	global mode
	Log("=", "ignition cut")
	if mode != "parked":
		os.system("aplay -q audio/Recording_Stopped.wav &")
		GPIO.cleanup()
		os.system("./exit.sh &")
		Log("!", "stopped dashcam.py")
		time.sleep(1)
		exit(0)
GPIO.add_event_detect(15, GPIO.FALLING, callback=ignition_cut, bouncetime=1000)

# Manual event button pressed
def manual_event(channel):
	Log("-", "manual event")
	os.system("aplay -q audio/Event_Stored.wav &")
	# Set flag to store events
	f = open('dashcam.event', 'w')
	f.write('true\n')
	f.close()
GPIO.add_event_detect(12, GPIO.FALLING, callback=manual_event, bouncetime=500)

# Main program loop
while True:
	try:
		report = session.next()
		# Print full report to see what fields are present		
		#print report
		#if report['class'] == 'TPV':
			#if hasattr(report, 'time'):
			#	Log("G", report.time)
			#if hasattr(report, 'lon'):
			#	print "Long = %f" %report.lon
			#if hasattr(report, 'lat'):
			#	print "Lat = %f" %report.lat
			#if hasattr(report, 'speed'):
			#	speed = report.speed * gps.MPS_TO_MPH
			#	print "Speed = %f" % speed
			#if hasattr(report, 'alt'):
			#	print "Altitude = %f" % report.alt
	except KeyError:
		pass
	except KeyboardInterrupt:
		quit()
	except StopIteration:
		session = None
		print "GPSD has terminated"
