"""
Base HTTP client for inter-service communication
"""
import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseServiceClient:
    """
    Base class for service-to-service HTTP communication
    Provides common HTTP methods with error handling, retry logic, and timeout management
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the service client

        Args:
            base_url: Base URL of the service (e.g., "http://player-service:8000")
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ScoutPro-ServiceClient/2.0"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute GET request

        Args:
            endpoint: API endpoint (e.g., "/api/v2/players/123")
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        try:
            if not self._client:
                raise RuntimeError("Client not initialized. Use async with context manager.")

            logger.debug(f"GET {self.base_url}{endpoint} params={params}")

            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for GET {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for GET {endpoint}: {str(e)}")
            raise

    async def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute POST request

        Args:
            endpoint: API endpoint
            data: JSON payload

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        try:
            if not self._client:
                raise RuntimeError("Client not initialized. Use async with context manager.")

            logger.debug(f"POST {self.base_url}{endpoint}")

            response = await self._client.post(endpoint, json=data)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for POST {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for POST {endpoint}: {str(e)}")
            raise

    async def _put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute PUT request

        Args:
            endpoint: API endpoint
            data: JSON payload

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        try:
            if not self._client:
                raise RuntimeError("Client not initialized. Use async with context manager.")

            logger.debug(f"PUT {self.base_url}{endpoint}")

            response = await self._client.put(endpoint, json=data)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for PUT {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for PUT {endpoint}: {str(e)}")
            raise

    async def _delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Execute DELETE request

        Args:
            endpoint: API endpoint

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        try:
            if not self._client:
                raise RuntimeError("Client not initialized. Use async with context manager.")

            logger.debug(f"DELETE {self.base_url}{endpoint}")

            response = await self._client.delete(endpoint)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for DELETE {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for DELETE {endpoint}: {str(e)}")
            raise

    async def health_check(self) -> bool:
        """
        Check if the service is healthy

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self._get("/health")
            return response.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"Health check failed for {self.base_url}: {str(e)}")
            return False
