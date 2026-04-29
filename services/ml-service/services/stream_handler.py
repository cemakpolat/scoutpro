import asyncio
import logging
from shared.messaging.kafka_consumer import Consumer
from config.settings import get_settings
from services.feature_pipeline import FeatureEngineeringPipeline

logger = logging.getLogger(__name__)
settings = get_settings()

class MLFeatureStreamProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.consumer = Consumer(
            topic='raw.events',
            group_id='ml_service_feature_engineering'
        )
        self.pipeline = FeatureEngineeringPipeline()
        self.running = False
        
    async def start(self):
        self.running = True
        logger.info("Starting ML Feature Stream Processor...")
        await self.consumer.start()
        
        try:
            async for message in self.consumer.consume():
                if not self.running:
                    break
                    
                await self.process_event(message.value)
                
                # Manually commit offset
                if not self.settings.kafka_auto_commit:
                    await self.consumer.commit()
                    
        except Exception as e:
            logger.error(f"Error in ML feature stream: {e}")
            raise

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("ML Feature Stream Processor stopped")

    async def process_event(self, event_data: dict):
        """
        Consume raw event and extract features into tensors
        """
        match_id = event_data.get('match_id')
        event_type = event_data.get('type')
        
        if not match_id or not event_type:
            return

        try:
            # Apply feature engineering to create standardized tensors
            features = self.pipeline.process_event_to_features(event_data)
            
            if 'pass_tensor' in features:
                tensor = features['pass_tensor']
                # For Phase 2, this is a placeholder where you would invoke a PyTorch model:
                # pass_prob = self.model.predict(tensor)
                # logger.debug(f"Computed Pass Probability: {pass_prob}")
                pass
                
        except Exception as e:
            logger.error(f"Failed to extract features for event {event_type}: {e}")
