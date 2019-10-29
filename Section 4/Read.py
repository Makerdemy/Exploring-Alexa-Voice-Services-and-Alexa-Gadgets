from time import sleep
import sys
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
reader = SimpleMFRC522()

try:
	while True :
		print ("Hold a Tag near the Reader")
		id,text=reader.read()
		if id is None :
			print("No id Read")
		else :
			print("ID : %s \n Text : %s" % (id,text))
except KeyboardInterrupt:
	GPIO.cleanup()
	raise
			
