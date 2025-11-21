import json
import time
from io import BytesIO

from confluent_kafka import Consumer, Producer
from fastavro import parse_schema, schemaless_reader, schemaless_writer

# 1) Load schema
with open("avro_schemas/order.avsc") as f:
    schema = json.load(f)

parsed_schema = parse_schema(schema)

# 2) Consumer config
consumer_config = {
    "bootstrap.servers": "localhost:29092",
    "group.id": "orders-consumer-group",
    "auto.offset.reset": "earliest"
}
consumer = Consumer(consumer_config)

# 3) Producer for DLQ
producer_config = {
    "bootstrap.servers": "localhost:29092"
}
dlq_producer = Producer(producer_config)


def avro_deserialize(value_bytes: bytes) -> dict:
    buf = BytesIO(value_bytes)
    return schemaless_reader(buf, parsed_schema)


def avro_serialize(record: dict) -> bytes:
    buf = BytesIO()
    schemaless_writer(buf, parsed_schema, record)
    return buf.getvalue()


def send_to_dlq(original_msg, error_reason: str):
    """Send bad message to DLQ with error info."""
    dlq_value = {
        "error": error_reason,
        "topic": original_msg.topic(),
        "partition": original_msg.partition(),
        "offset": original_msg.offset(),
        "key": original_msg.key().decode("utf-8") if original_msg.key() else None,
        "raw_value_hex": original_msg.value().hex()
    }

    # encode DLQ message as JSON (simpler)
    dlq_producer.produce(
        topic="orders_dlq",
        key=original_msg.key(),
        value=json.dumps(dlq_value).encode("utf-8")
    )
    dlq_producer.poll(0)
    print(f"Sent to DLQ: {dlq_value}")


def process_order(order: dict):
    """
    Simulate processing.
    We will artificially fail on some condition to demonstrate retry/DLQ.
    """
    # Example: fail if product is "Item3"
    if order["product"] == "Item3":
        raise RuntimeError("Simulated processing error for Item3")

    # otherwise, pretend processing is OK
    print(f"Processed order: {order}")


def main():
    consumer.subscribe(["orders"])

    total_price = 0.0
    count = 0

    print("Starting consumer...")

    try:
        while True:
            msg = consumer.poll(1.0)  # timeout seconds

            if msg is None:
                continue

            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            try:
                order = avro_deserialize(msg.value())
            except Exception as e:
                print(f"Deserialization error: {e}")
                send_to_dlq(msg, f"Deserialization failed: {e}")
                consumer.commit(msg)  # skip this message
                continue

            # Retry logic
            max_retries = 3
            attempt = 0
            success = False

            while attempt < max_retries and not success:
                try:
                    process_order(order)
                    success = True
                except Exception as e:
                    attempt += 1
                    print(f"Processing failed (attempt {attempt}/{max_retries}): {e}")
                    time.sleep(1)  # small delay before retry

            if not success:
                # permanent failure -> DLQ
                send_to_dlq(msg, "Max retries exceeded during processing")
                consumer.commit(msg)  # move on to next message
                continue

            # If processing succeeded, update running average
            total_price += order["price"]
            count += 1
            running_avg = total_price / count

            print(f"Running average price after {count} orders: {running_avg:.2f}")

            # commit offset so we don't reprocess on restart
            consumer.commit(msg)

    except KeyboardInterrupt:
        print("Stopping consumer...")

    finally:
        consumer.close()
        dlq_producer.flush()


if __name__ == "__main__":
    main()
