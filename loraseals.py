import eventlet
import json
from flask import Flask, render_template , request
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
from datetime import datetime
import time ,sched
#from sqlalchemy import Table,Column,Integer, String ,MetaData, ForeignKey
import sqlalchemy as db
import sqlite3
import threading

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = '192.168.16.187'
app.config['MQTT_BROKER_PORT'] = 1883
#app.config['MQTT_USERNAME'] = 'lynxemi'
#app.config['MQTT_PASSWORD'] = 'lyn*em!'
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

# Parameters for SSL enabled
# app.config['MQTT_BROKER_PORT'] = 8883
# app.config['MQTT_TLS_ENABLED'] = True
# app.config['MQTT_TLS_INSECURE'] = True
# app.config['MQTT_TLS_CA_CERTS'] = 'ca.crt'

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)
engine = db.create_engine('sqlite:///loraseals.db',echo =True,)
connection = engine.connect()
conn = sqlite3.connect('loraseals.db')

@mqtt.on_connect()
def handle_connect(client,userdata,flags,rc):
   
    mqtt.subscribe('application/2/device/#')    
    handle_connect.seals = []
    


@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    mqtt.publish(data['topic'], data['message'])


@socketio.on('subscribe')
def handle_subscribe(json_str):
    data = json.loads(json_str)
    mqtt.subscribe(data['topic'])
    


@socketio.on('unsubscribe_all')
def handle_unsubscribe_all():
    mqtt.unsubscribe_all()


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    print("------------------->")
    print(data['payload'])
    handle_mqtt_message.clientData = data['payload'] 
    x = json.loads(data['payload']) 
    handle_mqtt_message.isOffline = False
    handle_mqtt_message.offlineSeal = ""
    socketio.emit('mqtt_message', data=data)
    socketio.emit('mqtt_time',data = time.strftime("%H:%M",time.localtime())+':'+x['deviceName'])
    if handle_connect.seals != []:
          if next((item for item in handle_connect.seals if item['name'] == x['deviceName']),None) == None:   
                  timestamp = str(time.time()).split('.') 
                  if(x['object']['optlocked']== True and x['object']['swlocked'] == True):
                      curr_status = 1
                  else:
                      curr_status = 0  
                  handle_connect.seals.append({'name':x['deviceName'],'status':curr_status,'time':int(timestamp[0]),'deviceId':x['devEUI']})
                
   
    def monitor_seals():
            if handle_connect.seals == []:
                timestamp = str(time.time()).split('.')
                if(x['object']['optlocked']== True and x['object']['swlocked'] == True):
                    curr_status = 1
                else:
                      curr_status = 0  
                handle_connect.seals.append({'name':x['deviceName'],'status':curr_status,'time':int(timestamp[0]),'deviceId':x['devEUI']})
                
            for item in handle_connect.seals:               
 
                if(item.get('name') == x['deviceName']):
                #    item.update({'count': item['count']+1})
                   timestamp = str(time.time()).split('.')
                   item.update({'time':int(timestamp[0])})
                   
                   
                # date_time_obj_now = datetime.fromtimestamp(time.time())
                # date_time_obj_item = datetime.fromtimestamp(item.get('time'))
            for item in handle_connect.seals:
                date_time_obj_item = datetime.fromtimestamp(item.get('time'))                    
                print('uuuuuuuuuu')
                print(date_time_obj_item.time())
                print("Time Difference from Current Time")
                ts = str(time.time()).split('.')
                date_time_obj_now = datetime.fromtimestamp(int(ts[0]))
                diff = date_time_obj_now - date_time_obj_item
                res = divmod(diff.total_seconds(),60)
                print(int(res[0]))
                if int(res[0]) > 1 :
                    handle_mqtt_message.offlineSeal = item
                    handle_mqtt_message.isOffline = True
                    handle_connect.seals.remove(item)
                    print(item)
                                 
    print("======= Monitoring ==============")
    print(handle_connect.seals)
    monitor_seals()
    
   
   

    metadata = db.MetaData(engine)
    seals = db.Table('seals',metadata,    
         db.Column('sealname',db.String(50)),
         db.Column('sealstatus',db.Integer),
         db.Column('timestamp',db.String),
         db.Column('deviceId',db.String)
             )

    # sealstatus = db.Table('sealstatus',metadata,    
    #      db.Column('sealname',db.String(50)),
    #      db.Column('sealstatus',db.Integer),
    #      db.Column('timestamp',db.String),
    #          )

    logtable = db.Table('logtable',metadata,    
         db.Column('sealname',db.String(50)),
         db.Column('sealstatus',db.Integer),
         db.Column('timestamp',db.String),
         db.Column('deviceId',db.String)
             )
         
    if not engine.dialect.has_table(engine,'seals'):
        metadata = db.MetaData(engine)
        seals = db.Table('seals',metadata,    
         db.Column('sealname',db.String(50)),
         db.Column('sealstatus',db.Integer),
         db.Column('timestamp',db.String),
         db.Column('deviceId',db.String)
             )
        metadata.create_all()

    # if not engine.dialect.has_table(engine,'sealstatus'):
    #     metadata = db.MetaData(engine)
    #     sealstatus = db.Table('sealstatus',metadata,    
    #         db.Column('sealname',db.String(50)),
    #         db.Column('sealstatus',db.Integer),
    #         db.Column('timestamp',db.String),
    #             )
    #     metadata.create_all()

    if not engine.dialect.has_table(engine,'logtable'):
        metadata = db.MetaData(engine)
        logtable = db.Table('logtable',metadata,    
            db.Column('sealname',db.String(50)),
            db.Column('sealstatus',db.Integer),
            db.Column('timestamp',db.String),
            db.Column('deviceId',db.String)
                )
        metadata.create_all()

   
    
   

    cur = conn.cursor()
    cur1 = conn.cursor()
    cur2 = conn.cursor()
     
    cur.execute("SELECT * FROM {tn} WHERE deviceId =? " .\
    format(tn='seals'),(x['devEUI'],) )

    
    
    sealExists = cur.fetchone()
    #sealstatusExists = cur1.fetchone()
    logtableExists = cur2.fetchone()
    
    
    
    if  not sealExists:
        
        timestampStr = datetime.now()
        if(x['object']['optlocked']== True and x['object']['swlocked'] == True):
            curr_status = 1
         
        else:
                      curr_status = 0 
        ins = seals.insert().values(sealname = x['deviceName'],sealstatus = curr_status,timestamp = timestampStr,deviceId = x['devEUI'] )   
        ins1 = logtable.insert().values(sealname = x['deviceName'],sealstatus = curr_status,timestamp = timestampStr )       
        connection.execute(ins)
        connection.execute(ins1)
        socketio.emit('refresh',data="")
    
   

    if sealExists:
        if(x['object']['optlocked'] == True and x['object']['swlocked']== True):
            resultant = 1
        else:
            resultant = 0
        if sealExists[1] !=  resultant :            
            # print(sealExists[1])
            # print(x['object']['optlocked'])
            # print(x['object']['swlocked'])
            # print(x['deviceName'],x['object']['optlocked'])
            timestampStr = datetime.now()
            if(x['object']['optlocked']== True and x['object']['swlocked'] == True):
                curr_status = 1
            
            elif(x['object']['swlocked'] == False):
                print("*************")
                curr_status = 0 
            ins = seals.update().where(seals.c.sealname == x['deviceName']).values(sealstatus = curr_status,timestamp = timestampStr,deviceId = x['devEUI'] )
            ins1 = logtable.insert().values(sealname = x['deviceName'],sealstatus = curr_status,timestamp = timestampStr,deviceId = x['devEUI']) 
            connection.execute(ins)
            connection.execute(ins1)
            socketio.emit('refresh',data="")
           

   
        

    if(handle_mqtt_message.isOffline):
       
        timestampStr = datetime.now()
        item =  handle_mqtt_message.offlineSeal
        ins = seals.update().where(seals.c.sealname == item['name']).values(sealstatus = 3,timestamp = timestampStr,deviceId = item['deviceId'] )
        ins1 = logtable.insert().values(sealname = item['name'],sealstatus = 3,timestamp = timestampStr,deviceId = item['deviceId'])
        connection.execute(ins)
        connection.execute(ins1)
        handle_mqtt_message.isOffline = False
        socketio.emit('refresh',data="")
             

@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
     print(level, buf)


@app.route('/')
def index():
    user = {'username':'immanuel'}
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seals")
    results = cursor.fetchall()
    
    #return render_template('home.html',data= handle_mqtt_message.clientData, my_list=[0,1,2])
    return render_template('test.html',data= list(results))


@app.route('/logpage')
def index1():
    sealname =  request.args.get('sealname')
    print("--- seal name --- ",sealname)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM {tn} WHERE sealname =? " .\
    format(tn='logtable'),(sealname,) )
    data = cursor.fetchall()
    return render_template('logpage.html' ,data= list(data) ,sealname= sealname)

if __name__ == '__main__':
    # important: Do not use reloader because this will create two Flask instances.
    # Flask-MQTT only supports running with one instance
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=False)
    