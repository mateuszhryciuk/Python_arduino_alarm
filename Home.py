from flask import Flask, render_template,request
import ADAnalyzer as ADA
import threading

ard = ADA.ADAnalyzer('/dev/ttyUSB0',9600)

'''
Initaializg object for arduino comunication
'''



app = Flask(__name__)
@app.route("/", methods=['GET', 'POST'])
def home():
    mess = request.form.get('button')
    '''
    Majority of job ard object does
    Web server sends on/off message to ard and gets data from controller 
    '''

    print(mess)
    if mess == "OFF" or mess =="ON":
        ard.write_data(mess)
    data = ard.get_data()
    print(data)

    temp = data.get('temperature')
    humidity = data.get('humidity')
    doors = data.get('door_open')
    if doors == "1":
        doors = "open"
    elif doors == "0":
        doors = "closed"
    else :
        doors = None
    alarm = data.get('alarm_status')
    manual = data.get('manual_status')

    return render_template('Home.html', temp=temp,humidity=humidity,doors=doors,alarm=alarm,manual=manual)

if __name__=='__main__':

    app.run(host='0.0.0.0' , debug = True , threaded = True )
