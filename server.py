import pika
import time

connection = pika.BlockingConnection()

channel = connection.channel()

channel.exchange_declare(exchange='updates',
                         exchange_type='fanout')

for i in range(3):
    time.sleep(5)
    update_name = 'update {}'.format(i)
    update_body = 'this is update {} body'.format(i)
    print('Publishing {} to the people'.format(update_name))
    channel.basic_publish(exchange='updates',
                          routing_key=update_name,
                          body=update_body)

connection.close()