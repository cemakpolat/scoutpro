import json
import logging
from kafka import KafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskWorker")

def main():
    consumer = KafkaConsumer(
        'batch.historical.ingestion.requested',
        bootstrap_servers=['kafka:29092'],
        auto_offset_reset='smallest',
        group_id='batch-worker-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    logger.info("Task Worker initialized, listening to batch queue...")
    
    for message in consumer:
        job = message.value
        logger.info(f"Picked up historical batch job: {job.get('job_id')}")
        # In a full implementation, this triggers the data-sync-service provider batch logic
        # and then emits progress updates to 'batch.historical.completed' or a realtime websocket topic

if __name__ == "__main__":
    main()
