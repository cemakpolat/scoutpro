"""
WebSocket Server - Main Application
"""
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from websocket.manager import ConnectionManager

settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://api-gateway:3001,http://localhost:3001,http://localhost:5173,http://localhost:5174",
    ).split(",")
    if o.strip()
]

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "subscribe":
                    topic = message.get("topic")
                    await manager.subscribe(websocket, topic)

                elif message_type == "unsubscribe":
                    topic = message.get("topic")
                    await manager.unsubscribe(websocket, topic)

                elif message_type == "ping":
                    await manager.send_personal_message(
                        websocket,
                        {"type": "pong"}
                    )

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error("Invalid JSON received")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/{user_id}")
async def websocket_user_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint with user identification"""
    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "subscribe":
                    topic = message.get("topic")
                    await manager.subscribe(websocket, topic)

                elif message_type == "unsubscribe":
                    topic = message.get("topic")
                    await manager.unsubscribe(websocket, topic)

                elif message_type == "ping":
                    await manager.send_personal_message(
                        websocket,
                        {"type": "pong"}
                    )

            except json.JSONDecodeError:
                logger.error("Invalid JSON received")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.service_name}")

    try:
        from kafka_bridge.event_bridge import start_bridge
        logger.info("Starting Kafka-WebSocket bridge...")
        asyncio.create_task(start_bridge(manager))
        logger.info(f"{settings.service_name} started successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info(f"Shutting down {settings.service_name}")
    try:
        from kafka_bridge.event_bridge import stop_bridge
        await stop_bridge()
        logger.info("Kafka-WebSocket bridge stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title="WebSocket Server",
    description="ScoutPro Real-time WebSocket Server",
    version="2.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "2.0.0",
        "active_connections": manager.get_connection_count()
    }


@app.get("/stats")
async def get_stats():
    """Get WebSocket server statistics"""
    return {
        "active_connections": manager.get_connection_count(),
        "subscriptions": {
            topic: manager.get_topic_subscriber_count(topic)
            for topic in ["live.events", "match.updates", "player.events"]
        }
    }


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": "2.0.0",
        "websocket_url": "/ws",
        "active_connections": manager.get_connection_count()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug
    )
