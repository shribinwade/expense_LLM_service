import os
import sys
import time
import logging

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from flask import Flask, json, request, jsonify
from app.service.messageService import MessageService

app = Flask(__name__)
app.config.from_pyfile('config.py')

messageService = MessageService()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_producer = None
KAFKA_TOPIC = 'expense_service'


def get_producer():
    """Lazily create the Kafka producer on first use, with retry."""
    global _producer
    if _producer is not None:
        return _producer

    bootstrap = f"{os.getenv('KAFKA_HOST')}:{os.getenv('KAFKA_PORT')}"

    retries = 5
    delay = 2
    for attempt in range(1, retries + 1):
        try:
            _producer = KafkaProducer(
                bootstrap_servers=bootstrap,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                request_timeout_ms=5000,
            )
            logger.info("Connected to Kafka at %s", bootstrap)
            return _producer
        except NoBrokersAvailable:
            logger.warning("Kafka not reachable at %s (attempt %d/%d)",
                           bootstrap, attempt, retries)
            time.sleep(delay)

    logger.error("Could not connect to Kafka after %d attempts", retries)
    return None


@app.route('/v1/ds/message', methods=['POST'])
def handle_message():
    user_id = request.headers.get('x-user-id')
    if not user_id:
        return jsonify({'error': 'x-user-id header is required'}), 400

    body = request.get_json(silent=True) or {}
    message = body.get('message')
    if not message:
        return jsonify({'error': 'message is required'}), 400

    result = messageService.process_message(message)

    if isinstance(result, list):
        return jsonify([item.dict() for item in result])

    if result is not None and hasattr(result, "dict"):
        payload = result.dict()
        payload['user_id'] = user_id  # expense service now receives this

        producer = get_producer()
        if producer is not None:
            try:
                # key=user_id keeps one user's events ordered in the same partition
                producer.send(KAFKA_TOPIC, key=user_id, value=payload)
            except Exception:
                logger.exception("Failed to publish to Kafka")
        else:
            logger.error("Kafka producer unavailable; message not published")

        return jsonify(payload)

    return jsonify(result)


@app.route('/', methods=['GET'])
def handle_get():
    return 'hello world'


@app.route('/v1/ds/health', methods=['GET'])
def health_check():
    return 'OK'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8010, debug=False, use_reloader=False)