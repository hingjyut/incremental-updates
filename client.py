#!/usr/bin/env python
import pika
import uuid
import json
from hashlib import blake2b

from common import substitute_range

class Client:

    
    def __init__(self, software_name):
        self.software_name = software_name
        # initializes a connection and a channel
        self.connection = pika.BlockingConnection()
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='{} updates'.format(software_name), exchange_type='fanout')
        
        filename = "{}.json".format(self.software_name)
        f = None
        # if json file exists, gets client uuid and current version back, and uses uuid to communicate with server
        try:
            f = open(filename, "r")
            file_content = json.loads(f.read())
            f.close()

            self.client_uuid = file_content['client-uuid']
            self.current_version = file_content['current-version']
            self.latest_version_hash = blake2b(bytes(self.current_version, encoding="utf-8")).hexdigest()

        # if json file doesn't exist, that means this client is the first client who trys to connect to this server
        # it sends a request to server and waits for response
        except IOError:
            new_client_result = self.channel.queue_declare(queue='', exclusive=True)
            self.callback_queue = new_client_result.method.queue
            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self.on_response,
                auto_ack=True)

            response = self.call()
            self.client_uuid = response['client-uuid']
            self.current_version = response['latest-version']
            self.latest_version_hash = response['latest-version-hash']

        # after we get uuid and latest version, client listens to server to 
        new_update_result = self.channel.queue_declare(queue=self.client_uuid, exclusive=False)
        self.update_queue = new_update_result.method.queue
        # binds client's update queue to server's update queue to get all update informations
        self.channel.queue_bind(exchange='{} updates'.format(software_name),
                                queue=self.update_queue)
        # consume update info once client gets it
        self.channel.basic_consume(
            queue=self.update_queue, 
            on_message_callback=self.on_update, 
            auto_ack=True)
    
    def start(self):
        self.channel.start_consuming()

    # A callback function, returns wether the client gets updated
    def on_update(self, ch, method, properties, body):
        print("Got a new update!")

        update_body = json.loads(body)
        print(" old version: {}".format(self.current_version))
        self.current_version = substitute_range(
            update_body['update-begin'],
            update_body['update-end'],
            self.current_version,
            update_body['update-content'])
        print(" new version: {}".format(self.current_version))

        current_hash = blake2b(bytes(self.current_version, encoding="utf-8")).hexdigest()

        print(" hash before update: {}...".format(self.latest_version_hash[:10]))
        print(" hash after update: {}...".format(current_hash[:10]))

        self.latest_version_hash = update_body['latest-version-hash']
        print(" hash expect: {}...".format(self.latest_version_hash[:10]))

        if self.latest_version_hash == current_hash:
            print("Incremental update successful!")
        else:
            print("Rabbitmq did not deliver >:(")

    ''' 
    For every response from the server, this function checks if 
    the correlation_id is matched, if it is, saves the response to json file and breaks 
    the loop in call function
    '''
    def on_response(self, ch, method, props, body):
        print("Got a response")
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body)

    '''
        This function does the RPC work, it generates a correlation_id, publishes 
        correlation_id and the reply_to queue as a request to server, then it waits until 
        getting a response
    '''
    def call(self):
        print("About to ask for a new UUID")

        self.response = None
        self.corr_id = str(uuid.uuid4())    # generate a random correlation id to communicate
        # establish a rpc_queue, sends its request with correlation id and callback queue to server
        self.channel.basic_publish(
            exchange='',
            routing_key='{} client'.format(self.software_name),
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,   # reply_to: Used to name a callback queue.
                correlation_id=self.corr_id,    # correlation_id: Useful to correlate RPC responses with requests
            ),
            body='')
        # waiting for a response
        while self.response is None:
            self.connection.process_data_events()

        print("Got a new UUID")
        # store uuid and version into a json file
        return self.response

    # It stores information to a json file
    def store_info(self):
        filename = "{}.json".format(self.software_name)
        data = {
            'client-uuid': self.client_uuid,
            'current-version': self.current_version
        }

        json_object = json.dumps(data, indent = 4)

        # stores uuid into file if it is not in the file yet
        with open(filename, "w") as f:
            f.write(json_object)
            f.close()

# 
software_name = input("What is your software name? ")

client = Client(software_name)

try:
    client.start()
finally:
    client.store_info()
