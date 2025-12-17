#!/bin/sh
echo `date +%s` "! started dashcam.sh"

# Choose analogue audio output
amixer cset numid=3 1

# There is a bug with GPSD on the Raspberry Pi, so we kill it and restart
# This ensures it can see our USB GPS device
sudo killall gpsd
sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock
# sudo service ntp restart

# Start the dashcam python code
sudo python dashcam.py &

cd /home/pi
# set limit of rolling videos to 16GB
limit=16000000

echo "record" > dashcam.mode
echo "false" > dashcam.event
mode=$(cat dashcam.mode)
previous="dummy.h264"
current="dummy.h264"

while [ true ]; do 
	# Video disk space used
	used=$(du Video | tail -1 | awk '{print $1}')
	#echo `date +%s` "U Video" $used
	
	# Free up disk space if needed
	while [ $limit -le $used ]
	do
		remove=$(ls -1tr Video | grep .h264 | head -n 1)
		echo `date +%s` "-" $remove
		rm Video/$remove
		# Calculate disk space used
		used=$(du Video | tail -1 | awk '{print $1}')
	done

	# Check event store flag
	event=$(cat dashcam.event)
	if [ "$event" = "true" ]
		then
			# Copy files to event store
			if [ "$previous" != "dummy.h264" ]
				then
					echo `date +%s` "S" $previous
					cp Video/$previous Events &
			fi
			echo `date +%s` "S" $current
				cp Video/$current Events &
			
			# Reset event flag
			echo "false" > dashcam.event

			# Events disk space used
			used=$(du Events | tail -1 | awk '{print $1}')
			echo `date +%s` "U Events" $used
	fi

	# Check for new commands
	mode=$(cat dashcam.mode)
	if [ "$mode" = "exit" ]
		then
			echo `date +%s` "! stopped dashcam.sh"			
			# Shutdown the RPi, so we can safely remove power
			#sudo shutdown -h now
			exit
	fi
	if [ "$mode" = "record" ] || [ "$mode" = "parked" ]
		then
			# New file name
			previous=$current
			current=$(date +"%Y_%m_%d_%H:%M:%S.h264")
			echo `date +%s` "+" $current

			# Capture a 5 minute segment of video
			raspivid -n -b 9000000 -w 1280 -h 720 -o Video/$current -t 300000
	fi

	# Have commented the below code out as it crashes RPi sometimes

	# Log & check CPU temp
	#cpu_temp=$((`cat /sys/class/thermal/thermal_zone0/temp`/1000))
	#echo "T CPU $cpu_temp"

	# Log & check GPU temp
	#gpu_temp=$(/opt/vc/bin/vcgencmd measure_temp | cut -c6-7)
	#echo "T GPU $gpu_temp"
	
	# Temperature alarm?
	#if [ "$cpu_temp" -gt "70" ] || [ "$gpu_temp" -gt "70" ]
	#	then
	#		aplay -q audio/Temperature_Alarm.wav &
	#fi
done