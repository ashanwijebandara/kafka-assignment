import json
import random
import time
from io import BytesIO

from confluent_kafka import Producer
from fastavro import parse_schema, schemaless_writer

# 1) Load Avro schema
with open("avro_schemas/order.avsc") as f:
    schema = json.load(f)

parsed_schema = parse_schema(schema)

# 2) Create Kafka producer
producer_config = {
    "bootstrap.servers": "localhost:29092"  # matches docker-compose
}
producer = Producer(producer_config)


def avro_serialize(record: dict) -> bytes:
    """Serialize a Python dict to Avro bytes using the schema."""
    buf = BytesIO()
    schemaless_writer(buf, parsed_schema, record)
    return buf.getvalue()


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"Record produced to {msg.topic()} partition [{msg.partition()}] @ offset {msg.offset()}")


def main():
    products = ["Item1", "Item2", "Item3", "Item4"]

    order_id = 1001

    try:
        while True:
            record = {
                "orderId": str(order_id),
                "product": random.choice(products),
                "price": round(random.uniform(10.0, 100.0), 2)
            }

            value_bytes = avro_serialize(record)
            key_bytes = record["orderId"].encode("utf-8")

            producer.produce(
                topic="orders",
                key=key_bytes,
                value=value_bytes,
                callback=delivery_report
            )

            producer.poll(0)  # trigger callbacks
            print(f"➡️ Sent: {record}")

            order_id += 1
            time.sleep(1)  # send every 1 second (adjust for demo)

    except KeyboardInterrupt:
        print("Stopping producer...")

    finally:
        producer.flush()


if __name__ == "__main__":
    main()
