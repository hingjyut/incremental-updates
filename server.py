import pika
import time
import json
import uuid
from hashlib import blake2b

from common import *

connection = pika.BlockingConnection()

channel = connection.channel()

channel.exchange_declare(exchange='updates',
                         exchange_type='fanout')

def on_new_client_request(ch, method, props, body):
    global latest_version
    global latest_version_hash

    response = json.dumps({
        'client-uuid': uuid.uuid4(),
        'latest-version': latest_version,
        'latest-version-hash': latest_version_hash
    })

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     props.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)

software_name = input("What is your software name? ")
latest_version = input("Please type the first version below:\n")
latest_version_hash = blake2b(bytes(latest_version)).hexdigest()

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_new_client_request)

print(" [x] Awaiting RPC requests")
channel.start_consuming()

nb_updates = 0

while True:
    new_update_input = input("Do you want to publish an update?")

    if new_update_input != "yes" and new_update_input != "y":
        continue

    nb_updates += 1
    update_begin = int(input(" update begin: "))
    update_end = int(input(" update end: "))
    update_content = bytes(input(" update content: "))

    latest_version = substitute_range(update_begin, update_end, latest_version, update_content)
    latest_version_hash = blake2b(bytes(latest_version)).hexdigest()
    
    print('Publishing update {} to the people'.format(nb_updates))
    channel.basic_publish(exchange='{} updates'.format(software_name),
                          routing_key='',
                          body=json.dumps({
                              'update-content': update_content,
                              'latest-version-hash': latest_version_hash
                          }))

connection.close()