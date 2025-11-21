# Kafka Streaming Assignment – Producer, Consumer, Avro, Retry & DLQ

A comprehensive Kafka-based streaming pipeline for real-time data processing with advanced error handling and message aggregation.

## Project Overview

This project implements a production-like Kafka streaming architecture that demonstrates:

- **Avro serialization** for schema-validated message format
- **Real-time message consumption** and processing
- **Retry logic** with configurable retry attempts for failed messages
- **Dead Letter Queue (DLQ)** for permanent failures
- **Running average aggregation** of processed message data
- **Docker containerization** for easy Kafka setup

## Project Structure

```
kafka-assignment/
│
├── docker-compose.yml          # Kafka & Zookeeper configuration
├── README.md                   # This file
│
├── avro_schemas/
│   └── order.avsc              # Order message schema
│
├── src/
│   ├── producer.py             # Kafka producer implementation
│   └── consumer.py             # Kafka consumer with retry & DLQ logic
│
└── venv/                        # Python virtual environment
```

## 🔧 Prerequisites

### Required Software

- **Docker** + Docker Compose
- **Python** 3.8 or higher
- **Git** (optional but recommended)

### Python Dependencies

Install required packages:

```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Quick Start

### Step 1: Start Kafka & Zookeeper

From the project root directory:

```bash
docker compose up -d
```

Verify services are running:

```bash
docker ps
```

You should see two containers:
- `kafka-assignment-kafka-1`
- `kafka-assignment-zookeeper-1`

### Step 2: Run the Consumer (First)

Open your terminal and navigate to the project:

```bash
cd path/to/kafka-assignment
venv\Scripts\activate
python src\consumer.py
```

You will see logs like:

```
✔ Processed order: {'orderId': '1001', 'product': 'Item2', 'price': 45.99}
✔ Running average price: 45.99
⚠ Retrying failed message...
```

### Step 3: Run the Producer (Second Terminal)

Open a new terminal window and run:

```bash
cd path/to/kafka-assignment
venv\Scripts\activate
python src\producer.py
```

You will see logs like:

```
➡️ Sent: {'orderId': '1001', 'product': 'Item4', 'price': 56.52}
➡️ Sent: {'orderId': '1002', 'product': 'Item1', 'price': 23.45}
```

## System Architecture

### Producer

The producer generates random orders and sends them to Kafka:

1. Reads the Avro schema from `order.avsc`
2. Generates random orders with fields:
   - `orderId`: Unique order identifier
   - `product`: One of Item1, Item2, Item3, or Item4
   - `price`: Float value between 10.00 and 100.00
3. Serializes messages using Avro format
4. Sends to Kafka topic: `orders`

### Consumer

The consumer processes orders with advanced error handling:

1. **Deserialization**: Reads and deserializes Avro messages from the `orders` topic
2. **Processing Logic**:
   - If product is "Item3" → Deliberately fails (for demonstration)
   - Otherwise → Marks as successfully processed
3. **Retry Mechanism**: 
   - Attempts to process each failed message up to **3 times**
   - Logs each retry attempt
4. **Dead Letter Queue (DLQ)**:
   - After max retries exceeded, sends to `orders_dlq` topic
   - Includes original metadata: topic, partition, offset, key
   - Includes error reason and raw message (hex encoded)
5. **Aggregation**: 
   - Maintains running average price of all successfully processed messages
   - Updates and displays after each successful processing

## Avro Schema

The `order.avsc` schema defines the message structure:

```json
{
  "type": "record",
  "name": "Order",
  "namespace": "com.example",
  "fields": [
    { "name": "orderId", "type": "string" },
    { "name": "product", "type": "string" },
    { "name": "price", "type": "float" }
  ]
}
```

## Viewing Dead Letter Queue Messages

To inspect messages that failed processing:

```bash
docker exec -it kafka-assignment-kafka-1 bash
```

Inside the container, run:

```bash
kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic orders_dlq \
  --from-beginning
```

Expected output:

```json
{
  "error": "Max retries exceeded during processing",
  "topic": "orders",
  "partition": 0,
  "offset": 5,
  "key": "1006",
  "raw_value_hex": "08313030360a4974656d33f6281f42"
}
```

## Demonstration Checklist

For your project report, presentation, or viva, capture these screenshots:

- [ ] Output of `docker ps` showing running containers
- [ ] Producer terminal output with sent messages
- [ ] Consumer terminal showing:
  - [ ] Successfully processed orders
  - [ ] Retry attempts for failed messages
  - [ ] Running average price updates
- [ ] DLQ messages via Kafka console consumer
- [ ] System logs with timestamps

These artifacts prove the system meets all requirements.

## Stopping the System

To stop all containers:

```bash
docker compose down
```

To clean up volumes (optional):

```bash
docker compose down -v
```

## Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_retries` | 3 | Maximum retry attempts before sending to DLQ |
| `orders_topic` | orders | Kafka topic for producer/consumer |
| `dlq_topic` | orders_dlq | Dead Letter Queue topic |
| `bootstrap_servers` | localhost:9092 | Kafka broker address |
| `group_id` | order-consumer-group | Consumer group identifier |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker containers won't start | Ensure Docker daemon is running, check port conflicts |
| Module import errors | Verify virtual environment is activated, reinstall dependencies |
| Producer/Consumer won't connect | Confirm `docker ps` shows Kafka running on port 9092 |
| No messages in consumer | Ensure consumer starts before producer, check topic name |
| DLQ is empty | Verify Item3 orders are being produced (they trigger failures) |

## Key Technologies

- **Apache Kafka**: Distributed message streaming platform
- **Apache Avro**: Data serialization framework
- **confluent-kafka**: Python client for Kafka
- **Docker**: Containerization platform
- **Python 3.8+**: Implementation language

## Notes

- The system deliberately fails on "Item3" products to demonstrate retry and DLQ functionality
- Running averages only include successfully processed messages
- All retries are logged for debugging and audit purposes
- Messages in DLQ include hex-encoded raw values for inspection

## Support

For issues or questions regarding the implementation, refer to the inline code comments in `producer.py` and `consumer.py`.

##
See docker logs


Inspect DLQ with CLI
```
docker exec -it kafka-assignment-kafka-1 bash
```