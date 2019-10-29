import json
import logging
from agt import AlexaGadget
import sys
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
reader = SimpleMFRC522()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)



class AlphabetTester(AlexaGadget):

    def __init__(self):
        super().__init__()
        
        self.text = None

    def on_custom_alphabettester_testthealphabet(self, directive):

        payload = json.loads(directive.payload.decode("utf-8"))
        logger.info(payload['startGame'])
        startgame=str(payload['startGame'])
        if (startgame == "True"):
                print("Hold a tag near the reader")
                id, self.text = reader.read()
                if id is None :
                        print("It is None!")
                else:
                        self.fun()
                        print("ID: %s\nText: %s" % (id,self.text))
        else :
                print("Did not place the tag!")
                

    def on_custom_alphabettester_stoptest(self, directive):
       
        logger.info('Stopping the Game...')

    def fun(self):
        logger.info("Text:"+self.text)
        data=self.text
        self.text=data.strip()
        #self.alphabet = "A"
        #logger.info('Tag placed: Current letter ' + self.alphabet)
        payload = {'alphabet':self.text}
        logger.info(payload)
        self.send_custom_event('Custom.AlphabetTester', 'ReportAlphabet', payload)

if __name__ == '__main__':
    try:
        AlphabetTester().main()
    finally:
        GPIO.cleanup()
