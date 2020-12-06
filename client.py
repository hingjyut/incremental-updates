#!/usr/bin/env python
import pika
import uuid
import json
from hashlib import blake2b

from common import substitute_range

class Client:

    def __init__(self, software_name):
        self.software_name = software_name
        self.connection = pika.BlockingConnection()
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='{} updates'.format(software_name), exchange_type='fanout')
        
        filename = "{}.json".format(self.software_name)
        f = None
        try:
            f = open(filename, "r")
            file_content = json.loads(f.read())
            f.close()

            self.client_uuid = file_content['client-uuid']
            self.current_version = file_content['current-version']
            self.latest_version_hash = blake2b(bytes(self.current_version, encoding="utf-8")).hexdigest()

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

        new_update_result = self.channel.queue_declare(queue=self.client_uuid, exclusive=False)
        self.update_queue = new_update_result.method.queue
        self.channel.queue_bind(exchange='{} updates'.format(software_name),
                                queue=self.update_queue)
        self.channel.basic_consume(
            queue=self.update_queue, 
            on_message_callback=self.on_update, 
            auto_ack=True)
    
    def start(self):
        self.channel.start_consuming()

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

    def on_response(self, ch, method, props, body):
        print("Got a response")
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body)

    def call(self):
        print("About to ask for a new UUID")

        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='{} client'.format(self.software_name),
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body='')
        while self.response is None:
            self.connection.process_data_events()

        print("Got a new UUID")
        # store uuid and version into a json file
        return self.response

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


software_name = input("What is your software name? ")

client = Client(software_name)

try:
    client.start()
finally:
    client.store_info()


# ## This is a client file
# import pika
# import uuid
# import pathlib
# import json

# connection = pika.BlockingConnection()

# channel = connection.channel()

# channel.exchange_declare(exchange='updates', exchange_type='fanout')

# # exclusive = False : once the consumer connection is closed, the queue doesn't be deleted
# # use uuid4 to generate a random uuid for each client
# result = channel.queue_declare(queue=uuid.uuid4(), exclusive = False)

# queue_name = result.method.queue
# filename = "clien-uuid.txt"

# file = pathlib.Path(filename)
# # create a file if it doesn't exist
# if not file.exists ():
#    uuid_file = open(filename,"x")

# # stores uuid into file if it is not in the file yet
# with open(filename) as f:
#     if queue_name not in f.read():
#             f.write(queue_name)

# channel.queue_bind(exchange='updates', queue=queue_name)

# print('[*] Waiting for updates. To exit press CTRL+C')

# def callback(ch, method, properties, body):
#     print(" Get an update from server %r" % body)

# channel.basic_consume(
#         queue=queue_name, 
#         on_message_callback=callback, 
#         auto_ack=True)

# channel.start_consuming()
