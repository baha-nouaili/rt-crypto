import psycopg2

from rabbitmq_handler import RabbitMQHandler
from config.rabbitmq_config import QUEUES

queue_name = QUEUES.get("marquet_information_queue")
consumer = RabbitMQHandler("localhost", queue_name)


def handle_queue_message(ch, method, properties, body):
    print("Received message" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)


print("Listening for incoming messages...")
consumer.consume_messages(handle_queue_message)
