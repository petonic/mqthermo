#! /usr/bin/env python3
#
"""
mqthermo <low> <high>
"""

import sys
import paho.mqtt.client as mqtt
import time, threading, json
from pprint import *
import logging
import logzero
from logzero import logger
import datetime

import click


# Check temp every X seconds
INTERVAL = 15
temp_low = 32.0
temp_high = 38.0

# Default Log Format
LF_FORMAT = ('%(color)s[%(threadName)s %(levelname)1.1s %(asctime)s'
             '%(module)s:'
             '%(lineno)d]%(end_color)s %(message)s')
formatter = logzero.LogFormatter(fmt=LF_FORMAT)
logzero.setup_default_logger(formatter=formatter, level=logging.INFO)

#
NODE="sonoff-3d_printer"
TOPIC_GET_TEMP_CMD=['cmnd/{}/Status', '10']
TOPIC_GET_TEMP_RESP='stat/{}/STATUS10'
TOPIC_GET_FAN_RESP='stat/{}/POWER3'      # 'ON' or 'OFF
TOPIC_FAN_CMD=['cmnd/{}/Power3', None]
TOPIC_FAN_CMD_ON=['cmnd/{}/Power3', '1']
TOPIC_FAN_CMD_OFF=['cmnd/{}/Power3', '0']

PAYLOAD_STATUS = 'StatusSNS'
PAYLOAD_FAN_STATE = ''

# Timeouts

TO_SECS = 20

glob_e = None
glob_payload = []

#
SENSOR_TYPE = 'DS18B20'

# MQTT General
MQTT_BROKER_IP='192.168.86.2'
MQTT_PORT = 1883
MQTT_USER = 'ha-mqtt'
MQTT_PASSWORD = 'asdfZXC12'

client = None
fan_running = False

def on_subscribe(client, userdata, mid, granted_qos):
    logger.info('Subscribed: %s QOS=%s, userdata = %s',
             repr(mid), repr(granted_qos), repr(userdata))



def on_message(client, userdata, mid):
    print('on_message: {}'.format(repr(mid.payload)))
    data = json.loads(mid.payload.decode())
    print('\t{}'.format(pformat(data)))
    if data[PAYLOAD_TYPE] == PAYLOAD_STATUS:
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
            logger.error("Exception occured detecting sensor in MQTT resp: %s: %s",
                repr(e), repr(mid.payload))


def on_connect(client, userdata, flags, rc):
    logger.debug("Connected with result code: %s ", repr(rc))
    if rc != 0:
        logger.error('RC should be 0 on successful connect, we got  %d',
                     rc)
        logger.error('Userdata is {}\nFlags is {}'.format(
                repr(userdata), repr(flags)))
    glob_e.set()


    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe(TOPIC_GET_TEMP_RESP.format(NODE))
    # client.message_callback_add(PAYLOAD_STATUS, on_message_status)
    # client.message_callback_add(PAYLOAD_FAN_STATE, on_message_fan_state)

import pudb
import threading

glob_e = None

def on_publish(client, userdata, mid):
    print('on_publish: {}'.format(repr(mid.payload)))

def req_resp_cb(client, userdata, mid):
    """Used to get response from request"""
    (expected_topic, sema) = userdata
    # logger.debug('*** payload is %s', repr(mid.payload))
    if len(mid.payload):
        payload = mid.payload.decode()
    else:
        payload = None
    logger.debug('rrcb: Received response message (exp: %s, rcv: %s) back, payload = %s',
                 expected_topic, mid.topic, repr(payload))

    if expected_topic.lower() == mid.topic.lower():
        logger.debug('rrcb: TRUE -- matched topics: %s, setting payload = %s',
                    expected_topic, payload)
        glob_payload.append(payload)
        sema.set()
    else:
        logger.info('rrcv: false -- topics don\'t match')

def req_resp(topic, payload, subscr_string=None):
    """Generalized function to send an MQTT topic/payload and listen
    for a response specified by the SUBSCR_STRING."""
    global glob_payload

    sema = threading.Event()        # Used to ensure we got response
    glob_payload = []
    client.user_data_set((subscr_string, sema))

    # First, subscribe to topic where we are expecting a response
    logger.debug('============= RR (topic, payload, subscr_string) = ({},{},{})'.format(
            repr(topic), repr(payload), repr(subscr_string)))

    if (subscr_string):
        logger.debug('RR: Adding CB for "%s"', subscr_string)
        client.message_callback_add(subscr_string, req_resp_cb)
        client.subscribe(subscr_string)

    logger.debug('Publishing topic "%s", pl = "%s"', topic,
                 repr(payload))
    client.publish(topic, payload=payload)

    if (subscr_string):
        logger.debug('Going to sleep, waiting for "%s", timeout = %s',
                     subscr_string, repr(TO_SECS))
        client.loop_start()
        if not sema.wait(TO_SECS):
            # Timeout instead of MQTT message
            logger.info('rr: topic (%s) received timeout on %d secs',
                     repr(subscr_string), TO_SECS)
            returned_payload = None
        else:
            returned_payload = glob_payload.pop()

        client.loop_stop()

        logger.debug('Received response back (%s, %s)', topic, returned_payload)
        client.message_callback_remove(subscr_string)
        client.unsubscribe(subscr_string)
        glob_e = None
        return returned_payload


    else:
        logger.debug('No callback specified')
        return None


def get_fan_status():
    global client
    logger.debug('get_fan_status: top, time is {}'.format(time.ctime()))

    fan_status = req_resp(TOPIC_FAN_CMD[0].format(NODE), # Send: Topic
             TOPIC_FAN_CMD[1],              # Send: Payload
             TOPIC_GET_FAN_RESP.format(NODE)) # Subscr: Topic

    return fan_status

def switch_fan(state):
    global client
    logger.info('Switching fan to {}'.format(state))

    result = req_resp(TOPIC_FAN_CMD_ON[0].format(NODE),  # Topic
             '1' if state else '0', None)




def get_temp():
    global client
    logger.debug('request_temp: top, time is {}'.format(time.ctime()))

    temp = req_resp(TOPIC_GET_TEMP_CMD[0].format(NODE), # Send: Topic
             TOPIC_GET_TEMP_CMD[1],              # Send: Payload
             TOPIC_GET_TEMP_RESP.format(NODE)) # Subscr: Topic

    return temp


@click.command()
@click.argument('temp_low', type=float)
@click.argument('temp_high', type=float)
def cli(temp_low, temp_high):
    global client
    global glob_e
    global TOPIC_GET_TEMP

    if temp_low >= temp_high:
        print('{}: low-temp cannot be higher than high-temp'.format(
                sys.argv[0]), file=sys.stderr)
        # pu.db
        cli.get_help(click.Context(cli))
        sys.exit(2)

    logger.debug('main: low = %s, high = %s',repr(temp_low), repr(temp_high))

    # Set up a threading event for the callbacks to use
    glob_e = threading.Event()
    sema = glob_e


    # Set up MQTT connection
    client = mqtt.Client("mqtherm", userdata=sema)               #create new instance

    # Add back in the following line when connected to Panchome
    client.username_pw_set(MQTT_USER, password=MQTT_PASSWORD)    #set username and password
    client.on_connect= on_connect                      #attach function to callback
    client.on_message= on_message                      #attach function to callback

    try:
        logger.debug('Trying to connect to Broker @ {}, Port #{}'.format(
                MQTT_BROKER_IP, MQTT_PORT))
        ret_val = client.connect(MQTT_BROKER_IP, port=MQTT_PORT)
        client.loop_start()
        logger.debug("On connect call, ret_val = {}".format(repr(ret_val)))
    except:
        e = sys.exc_info()[0]
        logger.fatal('Error connecting to MQTT Broker @ %s:%s: %s',
                  MQTT_BROKER_IP, MQTT_PORT, sys.exc_info()[1])
        logger.fatal('Is the MQTT Broker running right now?')
        sys.exit(20)


    while True:
        logger.debug('=' * 60)
        logger.debug('=' * 60)
        logger.debug('=' * 60)
        logger.debug('**** Top of while')
        import pprint

        fan_running = True if get_fan_status() == 'ON' else False

        if fan_running == None:
            logger.error('ML: error reading fan stat, restarting loop.......')
            continue

        temp = get_temp()

        if temp == None:
            logger.error('ML: error reading temperature, restarting loop.......')
            continue

        #logger.debug('Return string is {}'.format(repr(temp)))
        temp_json = json.loads(temp)
        #logger.debug('JSON of string is {}'.format(pprint.pformat(temp_json)))
        temp = float(temp_json['StatusSNS']['DS18B20']['Temperature'])
        logger.debug('Temp is {}'.format(repr(temp)))
        # temp = float(temp)

        logger.debug('Fan status is {}'.format(fan_running))
        print('{}: FanState = {}, low = {}, high = {}, curr = {}'.format(
                datetime.datetime.now(), fan_running, temp_low, temp_high, temp))
        if fan_running:
            logger.debug('==== FAN is RUNNING')
            if temp <= temp_low:
                logger.info('Turning fan off, curr temp is %s, limit %s',
                    repr(temp), repr(temp_low))
                switch_fan(False)
            else:
                logger.debug('Keeping Fan on at %s, still under limit of %s',
                    repr(temp), repr(temp_low))
        else:
            logger.debug('==== FAN IS NOT RUNNING')

            if temp >= temp_high:
                logger.info('Turning fan on, curr temp is %s, limit %s',
                    repr(temp), repr(temp_high))
                switch_fan(True)
            else:
                logger.debug('Keeping Fan off at %s, still under limit of %s',
                    repr(temp), repr(temp_high))

        logger.debug('Sleeping for {} seconds\n\n\n'.format(INTERVAL))
        time.sleep(INTERVAL)
