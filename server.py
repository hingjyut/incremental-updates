import pika

connection = pika.BlockingConnection()

channel = connection.channel()

def on_queue_declared(queue):
    channel.basic_publish('',
                        'test_routing_key',
                        'message body value',
                        pika.BasicProperties(content_type='text/plain',
                                            delivery_mode=1))

channel.queue_declare(queue='updates',
                      durable=True, 
                      exclusive=True, 
                      auto_delete=False, 
                      callback=on_queue_declared)


connection.close()