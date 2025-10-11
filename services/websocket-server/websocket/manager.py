"""
WebSocket Connection Manager
"""
import logging
import json
from typing import Dict, Set, Any
from fastapi import WebSocket
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and subscriptions"""

    def __init__(self):
        # Active connections: { websocket: user_info }
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}

        # Subscriptions: { topic: set(websockets) }
        self.subscriptions: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept and register a new connection"""
        await websocket.accept()

        self.active_connections[websocket] = {
            "user_id": user_id,
            "subscriptions": set()
        }

        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a connection"""
        if websocket in self.active_connections:
            # Remove from all subscriptions
            user_subs = self.active_connections[websocket]["subscriptions"]
            for topic in user_subs:
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(websocket)

            # Remove connection
            del self.active_connections[websocket]

            logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe a connection to a topic"""
        if websocket in self.active_connections:
            self.subscriptions[topic].add(websocket)
            self.active_connections[websocket]["subscriptions"].add(topic)

            logger.info(f"Client subscribed to {topic}")

            await self.send_personal_message(
                websocket,
                {
                    "type": "subscription_confirmed",
                    "topic": topic
                }
            )

    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe a connection from a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(websocket)

        if websocket in self.active_connections:
            self.active_connections[websocket]["subscriptions"].discard(topic)

            await self.send_personal_message(
                websocket,
                {
                    "type": "unsubscription_confirmed",
                    "topic": topic
                }
            )

    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""
        disconnected = []

        for websocket in self.active_connections.keys():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """Broadcast message to all subscribers of a topic"""
        if topic not in self.subscriptions:
            return

        disconnected = []

        for websocket in self.subscriptions[topic]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to topic subscriber: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_topic_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic"""
        return len(self.subscriptions.get(topic, set()))
