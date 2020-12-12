import pika
import time
import json
import uuid
from threading import Thread
from hashlib import blake2b

from common import *

software_name = input("What is your software name? ")

latest_version = input("Please type the first version below:\n")
latest_version_hash = blake2b(bytes(latest_version, encoding='utf8')).hexdigest()

def on_new_client_request(ch, method, props, body):
    global latest_version
    global latest_version_hash

    print("Got a new client request")

    # once server gets a request, it generates a random uuid for its client
    new_client_uuid = str(uuid.uuid4())
    response = json.dumps({
        'client-uuid': new_client_uuid,
        'latest-version': latest_version,
        'latest-version-hash': latest_version_hash
    })

    # server sends a response to client
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     props.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print("Just added new client {}".format(new_client_uuid))

# waiting for the first rpc request 
def listen_for_new_clients(software_name):
    connection = pika.BlockingConnection()
    channel = connection.channel()
    channel.queue_declare(queue='{} client'.format(software_name))
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='{} client'.format(software_name), 
                          on_message_callback=on_new_client_request)

    print(" [x] Awaiting RPC requests")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        pass
    finally:
        connection.close()

def publish_updates(software_name):
    global latest_version
    global latest_version_hash

    connection = pika.BlockingConnection()
    channel = connection.channel()
    channel.exchange_declare(exchange='updates',
                             exchange_type='fanout')
    nb_updates = 0

    # keep updating user's input
    while True:
        new_update_input = input("Do you want to publish an update?")

        if new_update_input != "yes" and new_update_input != "y":
            break

        nb_updates += 1
        update_begin = int(input(" update begin: "))
        update_end = int(input(" update end: "))
        update_content = input(" update content: ")

        print(" old version: {}".format(latest_version))
        latest_version = substitute_range(update_begin, update_end, latest_version, update_content)
        print(" new version: {}".format(latest_version))

        latest_version_hash = blake2b(bytes(latest_version, encoding='utf8')).hexdigest()
        
        print('Publishing update {} to the people'.format(nb_updates))
        channel.basic_publish(exchange='{} updates'.format(software_name),
                            routing_key='',
                            body=json.dumps({
                                'update-begin': update_begin,
                                'update-end': update_end,
                                'update-content': update_content,
                                'latest-version-hash': latest_version_hash
                            }))

    connection.close()

# start a thread to listen to new coming client
new_clients_thread = Thread(target=listen_for_new_clients, args=[software_name])
new_clients_thread.start()

# in this thread, keep listening if user wants to publish new updates, 
publish_updates(software_name)

new_clients_thread.join(1.0)