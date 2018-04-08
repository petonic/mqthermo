#! /usr/bin/env python3
#

import paho.mqtt.client as mqtt
import time, threading, json
from pprint import *
import logzero
import sys


# Check temp every X seconds
INTERVAL = 5
TEMP_FAN_ON = 32.0
TEMP_FAN_OFF = 38.0

#
NODE="sonoff-3d_printer"
TOPIC_GET_TEMP_CMD=['{}/cmnd/Status', '10']
TOPIC_GET_TEMP_RESP='{}/stat/STATUS10'
TOPIC_GET_FAN_RESP='{}stat/POWER3'      # 'ON' or 'OFF
TOPIC_FAN_CMD=['{}/cmnd/Power3', None]
TOPIC_FAN_CMD_ON=['{}/cmnd/Power3', '1']
TOPIC_FAN_CMD_OFF=['{}/cmnd/Power3', '0']

PAYLOAD_STATUS = 'StatusSNS'
PAYLOAD_FAN_STATE = ''

# Timeouts

TO_RETRIES = 5
TO_SECS = 5


#
SENSOR_TYPE = 'DS18B20'

# MQTT General
MQTT_BROKER_IP='panchome.local'
MQTT_PORT = 1883
MQTT_USER = 'ha-mqtt'
MQTT_PASSWORD = 'asdfZXC12'

client = None
fan_running = False

def manage_fan(temp):
    """Turns the fan (via MQTT) on or off based on the temperature and
    definitions of when to turn the fan on and off."""

def on_msg_fan(client, userdata, mid):
    payload = json.loads(mid.payload.decode())
    fan_running = True if payload == 'ON' else False

def on_msg_temperature(client, userdata, mid):
    temp= json.loads(mid.payload.decode())[SENSOR_TYPE]
    if temp['TempUnit'] != 'C':
        logger.error('Incorrect temp units, should be "C" not "%s"',
                     temp['TempUnit'])
        sys.exit(5)
    ret_temp = float(temp['Temperature'])
    return (ret_temp)


def on_message(client, userdata, mid):
    print('on_message: {}'.format(repr(mid.payload)))
    data = json.loads(mid.payload.decode())
    print('\t{}'.format(pformat(data)))
    if data[PAYLOAD_TYPE] == PAYLOAD_STATUS
    try:
        if not (SENSOR_TYPE in data[PAYLOAD_STATUS]):
            logger.error('Incorrect sensor type of %s, only support %s',
                         data[PAYLOAD_STATUS], SENSOR_TYPE)
            sys.exit(3)
        if data[PAYLOAD_STATUS][SENSOR_TYPE]['TempUnit'] != 'C':
            logger.error('Incorrect temp scale, should be C, but it is %s',
                  data[PAYLOAD_STATUS][SENSOR_TYPE]['TempUnit'])
            sys.exit(4)
        temp = float(data[PAYLOAD_STATUS][SENSOR_TYPE]['Temperature'])
        manage_fan(temp)

    except:
        import sys
        e = sys.exc_info()[0]
        logger.error("Exception occured detecting sensor in MQTT resp: %s: %s"%(
            repr(e), repr(mid.payload));


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC_GET_TEMP_RESP.format(NODE))
    client.message_callback_add(PAYLOAD_STATUS, on_message_status)
    client.message_callback_add(PAYLOAD_FAN_STATE, on_message_fan_state)

import pudb

def on_publish(client, userdata, mid):
    print('on_publish: {}'.format(repr(mid.payload)))

# import time, threading
# def foo():
#     print(time.ctime())
#     threading.Timer(10, foo).start()
#
# foo()

def request_temp):
    temp = pet_mqtt_reqresp(

def request_temp():
    global client
    print('request_temp: top, time is {}'.format(time.ctime()))
    threading.Timer(INTERVAL, request_temp)
    client.publish(TOPIC_GET_TEMP[0].format(NODE), TOPIC_GET_TEMP[1])

def get_temp():
    """Gets the current temperature by a) sending a request temp topic, and then
    b) waiting for the response.  Uses a series of timeouts provided by
    defaults."""



def main():
    global client

    # Set up MQTT connection
    client = mqtt.Client("mqtherm")               #create new instance
    client.username_pw_set(MQTT_USER, password=MQTT_PASSWORD)    #set username and password
    client.on_connect= on_connect                      #attach function to callback
    client.on_message= on_message                      #attach function to callback

    threading.Timer(INTERVAL, request_temp)
    client.connect(MQTT_BROKER_IP, port=MQTT_PORT)

    #time.sleep(10)

    client.loop_start()

    while True:
        logger.debug('Top of while')
        fan_running = get_fan_status()

        temp = get_temp()

        if fan_running:
            if temp >= TEMP_FAN_OFF:
                logger.info('Turning fan off, curr temp is %s, limit %s',
                    repr(temp), repr(TEMP_FAN_OFF))
                switch_fan(False)
            else:
                logger.debug('Fan on at %s, still under limit of %s',
                    repr(temp), repr(TEMP_FAN_OFF))
        else:
            if temp <= TEMP_FAN_ON:
                logger.info('Turning fan on, curr temp is %s, limit %s',
                    repr(temp), repr(TEMP_FAN_ON))
                switch_fan(False)
            else:
                logger.debug('Fan on at %s, still under limit of %s',
                    repr(temp), repr(TEMP_FAN_OFF))





        # Get fan status
        client.publish(TOPIC_GET_FAN_RESP[0].format(NODE), TOPIC_GET_TEMP[1])
        client.publish(TOPIC_GET_TEMP[0].format(NODE), TOPIC_GET_TEMP[1])
        sleep
        request_temp()
        time.sleep(60)




if __name__ == '__main__':
    main()
