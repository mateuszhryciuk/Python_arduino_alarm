
import threading
import serial
import time
import re
import queue
import smtplib

class ADAnalyzer:
    '''
    Initiate object with your device mount point as a string and int bound rate 9600
    for example : ard = ADA.ADAnalyzer('/dev/ttyUSB0',9600)
    Constructor sets up  attributes and starts loop thread analizing data from the controller
    to make things clear there are two methods you should use
    ADAnalyzer.get_data() returning data dictionary
    ADAanalyzer.write_data("ON") with string parameter "on" or "off" to switch alarm ON or OFF
    any other argument will be ignored by the controllerself.
    Then alarm is being triggered an email message is being send .
    Email setup has been hardcoded into the script for now and should be changed later on for
    external file or list .
    '''

    def __init__(self,device,baudrate):

        self._serialcom = serial.Serial(device,baudrate)
        self._datapattern = re.compile('(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+),[0-1],(ON)?(OFF)?,(M-ON)?(M-OFF)?')
        self._alarmpattern = re.compile('alarm!')
        self._message_sent = False
        self._mail= smtplib.SMTP('smtp.gmail.com',587)
        self._lock = threading.Lock()
        self._loop = threading.Thread(target = self._analize)
        self._loop.setDaemon(True)
        self._q = queue.Queue(maxsize=3)
        self._e = threading.Event()
        self._e.set()
        self._loop.start()

    def get_data(self):
        '''
        Returns data dictionary from the queue
        If the queue is empty method returns disctionary with "none" values

        '''
        try:
            return self._q.get(True,1)
        except:
            return {
            "temperature":"none",
            "humidity":"none",
            "door_open":"none",
            "alarm_status":"none",
            "manual_status":"none"
            }

    def write_data(self,onoff):
        '''
        Accepts string parameters "on" or "off" any other
        would be ignored by controller
        '''
        self._e.clear()
        self._serialcom.write(onoff.encode())
        self._e.set()

    def _read_data(self):
        '''
        internal use method reads serial input
        '''
        rawdata = self._serialcom.readline().decode()
        if rawdata :
            print("Raw data from controller : "+rawdata)
            return rawdata
        else :
            return False

    def _analize(self):
        '''
        Internal deamon thread method analizing data from the controller
        This method manage email sending
        Email setup is hardcoded here ...
        I decided to leave it here for now to keep the script not large
        It might be changed in the future iteration
        '''
        while True:
            self._e.wait()
            self._lock.acquire()
            try:
                data = self._read_data()
                if not data:
                    print ("reading serial error")

                if re.match(self._alarmpattern,data):

                    datadictionary = {
                    "temperature":"ALARM!!",
                    "humidity":"ALARM!!",
                    "door_open":"ALARM!!",
                    "alarm_status":"ALARM!!",
                    "manual_status":"ALARM!!"
                    }
                    try:
                        self._q.put(datadictionary, False)
                    except:
                        self._q.get()
                        self._q.put(datadictionary, False)

                    if self._message_sent == False :
                        print("sending alarm email message")
                        self._mail.connect("smtp.gmail.com",587)
                        self._mail.ehlo()
                        self._mail.starttls()
                        self._mail.ehlo()
                        self._mail.login("yourmail@gmail.com","password")
                        msg="Alarm !!!!"
                        self._mail.sendmail("yourmail@gmail.com","mateusz.hryciuk@outlook.com",msg)
                        self._mail.sendmail("yourmail@gmail.com","mat.hryciuk@gmail.com",msg)
                        #up to you how many email you want to inform
                        self._mail.quit()
                        self._message_sent = True

                if  re.match(self._datapattern,data):
                    datalist = data.split(",")
                    datadictionary = {
                    "temperature":datalist[0],
                    "humidity":datalist[1],
                    "door_open":datalist[2],
                    "alarm_status":datalist[3],
                    "manual_status":datalist[4]
                    }
                    print("ALL OK  !!!  queue data dictionary : ")
                    print(datadictionary)
                    try:
                        self._q.put(datadictionary, False)
                    except:
                        self._q.get()
                        self._q.put(datadictionary, False)
                else :
                    print ("data corupted")


            finally:
                self._lock.release()
