import pika
import json


class RabbitMQHandler:
    def __init__(self, host, queueName):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.queueName = queueName

    def setup_queue_for_publishing(self, exchange, routing_key):
        self.exchange = exchange
        self.routing_key = routing_key

        self.channel.queue_declare(queue=self.queueName, durable=True)
        self.channel.exchange_declare(exchange=exchange, exchange_type="direct")
        self.channel.queue_bind(
            queue=self.queueName,
            exchange=exchange,
            routing_key=routing_key,
        )
        return self

    def publish_message(self, message):
        print(f"sending message, {message}")
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.routing_key,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )

    def consume_messages(self, callback):
        self.channel.queue_declare(queue=self.queueName, durable=True)
        self.channel.basic_consume(queue=self.queueName, on_message_callback=callback)
        self.channel.start_consuming()

    def close_connection(self):
        self.connection.close()
