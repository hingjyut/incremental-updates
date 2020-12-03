## This is a client file
import pika

connection = pika.BlockingConnection()

channel = connection.channel()

channel.exchange_declare(exchange='updates', exchange_type='fanout')

result = channel.queue_declare(queue='', exclusive=True)

queue_name = result.method.queue

channel.queue_bind(exchange='updates', queue=queue_name)

print('[*] Waiting for updates. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(" Get an update from server %r" % body)

channel.basic_consume(
        queue=queue_name, 
        on_message_callback=callback, 
        auto_ack=True)

channel.start_consuming()
