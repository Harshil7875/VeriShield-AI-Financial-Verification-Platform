# backend/app/kafka_producer.py

import json
import os
import time
from kafka import KafkaProducer
from kafka.errors import KafkaError

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", "verishield_dlq")

# Global reference, but not created until first use
_producer = None

def get_producer():
    """
    Lazily create the KafkaProducer the first time it’s needed,
    avoiding connection attempts before Kafka is ready.
    """
    global _producer
    if _producer is not None:
        return _producer

    _producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        # optional: handle larger message sizes, timeouts, etc.
    )
    return _producer


def publish_event(topic: str, data: dict, max_retries: int = 3):
    """
    Publish an event with basic retry logic. On repeated failure, push to DLQ.
    """
    for attempt in range(1, max_retries + 1):
        try:
            producer = get_producer()  # Acquire or create the KafkaProducer
            future = producer.send(topic, data)
            record_metadata = future.get(timeout=10)
            # If successful, break out of the loop
            return
        except KafkaError as e:
            print(f"[Producer] Attempt {attempt} failed to publish: {e}")
            time.sleep(1)  # small backoff

    # If all attempts fail, send data to DLQ topic
    print("[Producer] All attempts failed, sending to DLQ.")
    try:
        producer = get_producer()
        producer.send(DLQ_TOPIC, {
            "original_topic": topic,
            "failed_data": data
        })
    except KafkaError as e:
        print(f"[Producer] Even DLQ publish failed: {e}")
