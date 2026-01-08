import pika
import json

def publish_event(event_type: str, data: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    channel = connection.channel()

    channel.exchange_declare(
        exchange="commerce.exchange",
        exchange_type="fanout"
    )

    channel.basic_publish(
        exchange="commerce.exchange",
        routing_key="",
        body=json.dumps({
            "eventType": event_type,
            "data": data
        })
    )

    connection.close()
