# consumer/kafka_consumer.py

import os
import json
import time
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
USER_CREATED_TOPIC = os.getenv("KAFKA_USER_CREATED_TOPIC", "user_created")
DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", "verishield_dlq")

consumer = KafkaConsumer(
    USER_CREATED_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='verishield-consumer-group',
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

# Producer for posting to DLQ if needed
dlq_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def run_consumer():
    print(f"[Consumer] Subscribed to {USER_CREATED_TOPIC}. Waiting for messages...")
    for msg in consumer:
        event = msg.value
        print(f"[Consumer] Received event: {event}")
        try:
            process_event(event)
        except Exception as e:
            print(f"[Consumer] Error processing event {event}: {e}")
            send_to_dlq(event, e)

def process_event(event_data, max_retries=3):
    """
    Example: we attempt to set user.is_verified = True, 
    simulating a successful KYC check. Basic retry logic included.
    """
    for attempt in range(1, max_retries + 1):
        try:
            with SessionLocal() as db:
                user_id = event_data.get("user_id")
                if user_id:
                    user = db.query(User).filter_by(id=user_id).first()
                    if user:
                        user.is_verified = True
                        db.commit()
                        db.refresh(user)
                        print(f"[Consumer] Verified user {user_id} on attempt {attempt}")
                        return
                    else:
                        print(f"[Consumer] User ID {user_id} not found in DB.")
                        return  # Not in DB, might not be an error
        except Exception as ex:
            print(f"[Consumer] Attempt {attempt} error: {ex}")
            time.sleep(1)
    # If we exhaust retries, raise exception to trigger DLQ
    raise RuntimeError(f"Failed to process event after {max_retries} attempts.")

def send_to_dlq(event_data, exception):
    """Push the problematic event to the DLQ topic for manual review."""
    dlq_message = {
        "failed_event": event_data,
        "error": str(exception),
        "timestamp": time.time()
    }
    try:
        dlq_producer.send(DLQ_TOPIC, dlq_message)
        print(f"[Consumer] Sent event to DLQ: {dlq_message}")
    except KafkaError as e:
        print(f"[Consumer] DLQ publish failed: {e}")

if __name__ == "__main__":
    run_consumer()
