"""
Credential Store for Credential Proxy

Loads service credentials from a JSON configuration file.
Provides credential injection for proxied requests.
"""

import json
import os
import logging
from dataclasses import dataclass
from typing import Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class ServiceCredential:
    """Configuration for a proxied service."""
    base_url: str
    auth_type: Literal["bearer", "header", "query"]
    credential: str
    auth_header: Optional[str] = None  # For auth_type="header"
    query_param: Optional[str] = None  # For auth_type="query"

    def inject_auth(self, headers: dict, url: str) -> tuple[dict, str]:
        """
        Inject authentication into request headers and/or URL.

        Args:
            headers: Request headers dict (will be modified)
            url: Request URL

        Returns:
            Tuple of (modified headers, modified URL)
        """
        headers = dict(headers)  # Copy to avoid modifying original

        if self.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.credential}"

        elif self.auth_type == "header":
            header_name = self.auth_header or "X-API-Key"
            headers[header_name] = self.credential

        elif self.auth_type == "query":
            param_name = self.query_param or "api_key"
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{param_name}={self.credential}"

        return headers, url


class CredentialStore:
    """
    Load and manage service credentials from a JSON configuration file.

    Expected JSON structure:
    {
        "service_name": {
            "base_url": "https://api.example.com",
            "auth_type": "bearer",
            "credential": "your-api-token",
            "auth_header": "X-Custom-Header",  // optional, for auth_type="header"
            "query_param": "api_key"           // optional, for auth_type="query"
        }
    }
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize credential store from config file.

        Args:
            config_path: Path to credentials.json. Defaults to same directory as this file.
        """
        self._credentials: dict[str, ServiceCredential] = {}

        if config_path is None:
            # Default to credentials.json in same directory
            config_path = os.path.join(os.path.dirname(__file__), "credentials.json")

        self._config_path = config_path
        self._load()

    def _load(self) -> None:
        """Load credentials from JSON file."""
        if not os.path.exists(self._config_path):
            logger.warning(f"Credentials file not found: {self._config_path}")
            logger.info("Create credentials.json from credentials.example.json")
            return

        try:
            with open(self._config_path, 'r') as f:
                config = json.load(f)

            for service_name, service_config in config.items():
                try:
                    self._credentials[service_name] = ServiceCredential(
                        base_url=service_config["base_url"],
                        auth_type=service_config["auth_type"],
                        credential=service_config["credential"],
                        auth_header=service_config.get("auth_header"),
                        query_param=service_config.get("query_param")
                    )
                    logger.info(f"Loaded credentials for service: {service_name}")
                except KeyError as e:
                    logger.error(f"Invalid config for service {service_name}: missing {e}")
                except Exception as e:
                    logger.error(f"Error loading service {service_name}: {e}")

            logger.info(f"Loaded {len(self._credentials)} service(s) from {self._config_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self._config_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")

    def get(self, service: str) -> Optional[ServiceCredential]:
        """
        Get credential configuration for a service.

        Args:
            service: Service name

        Returns:
            ServiceCredential if found, None otherwise
        """
        return self._credentials.get(service)

    def list_services(self) -> list[str]:
        """
        List all configured service names.

        Returns:
            List of service names
        """
        return sorted(self._credentials.keys())

    def has_service(self, service: str) -> bool:
        """
        Check if a service is configured.

        Args:
            service: Service name to check

        Returns:
            True if service exists in credential store
        """
        return service in self._credentials

    def reload(self) -> None:
        """Reload credentials from config file."""
        self._credentials.clear()
        self._load()
