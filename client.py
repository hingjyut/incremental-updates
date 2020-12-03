#!/usr/bin/env python
import pika
import uuid
import json

class Client(object):

    def __init__(self):
        self.connection = pika.BlockingConnection()
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='updates', exchange_type='fanout')
        result = self.channel.queue_declare(queue='', exclusive=False)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='updates',
            routing_key='',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n))
        while self.response is None:
            self.connection.process_data_events()
        # store uuid and version into a json file
        store_info(self.corr_id, int(self.response))
        return int(self.response)

    def store_info(self, client_uuid, version):
        filename = "clien-uuid.json"
        data = {client_uuid, version}
        json_object = json.dumps(data, indent = 4)

        # stores uuid into file if it is not in the file yet
        with open(filename, "w") as f:
            f.write(json_object)

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
