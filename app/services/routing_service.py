"""
Routing Service

This service interfaces with the HSL Routing API (Digitransit GraphQL API)
to fetch public transport routes and itineraries.

API Endpoint: https://api.digitransit.fi/routing/v2/hsl/gtfs/v1
Documentation: https://digitransit.fi/en/developers/apis/1-routing-api/
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from gql import Client, gql
from gql.transport.exceptions import TransportQueryError
from gql.transport.httpx import HTTPXAsyncTransport
from httpx import HTTPError, TimeoutException

from app.core.config import settings
from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary, Leg, Route, TransportMode
from app.schemas.location import Place

logger = logging.getLogger(__name__)

# Basic itinerary query
# This is the main query for fetching routes between two points
ITINERARY_QUERY = """
query GetItinerary(
    $originLat: CoordinateValue!
    $originLon: CoordinateValue!
    $destinationLat: CoordinateValue!
    $destinationLon: CoordinateValue!
    $first: Int
    $earliestDeparture: OffsetDateTime!
) {
    planConnection(
        origin: {
            location: {
                coordinate: {
                    latitude: $originLat,
                    longitude: $originLon
                }
            }
        }
        destination: {
            location: {
                coordinate: {
                    latitude: $destinationLat,
                    longitude: $destinationLon
                }
            }
        }
        first: $first
        dateTime: {
            earliestDeparture: $earliestDeparture
        }
    ) {
        edges {
            node {
                start
                end
                duration
                walkDistance
                walkTime
                legs {
                    mode
                    start {
                        scheduledTime
                    }
                    end {
                        scheduledTime
                    }
                    duration
                    distance
                    from {
                        name
                        lat
                        lon
                    }
                    to {
                        name
                        lat
                        lon
                    }
                    route {
                        shortName
                        longName
                        desc
                    }
                }
            }
        }
    }
}
"""


class RoutingServiceError(Exception):
    """Base exception for routing service errors."""


class RoutingAPIError(RoutingServiceError):
    """Raised when the HSL API returns an error."""


class RoutingNetworkError(RoutingServiceError):
    """Raised when network communication fails."""


class RoutingDataError(RoutingServiceError):
    """Raised when response data cannot be parsed."""


class RoutingService:
    """
    Service for interacting with HSL (Helsinki Regional Transport) Routing API.

    Uses GraphQL to query routes, itineraries, and transport information
    from the Digitransit platform.
    """

    def __init__(self):
        """
        Initialize HSL service with GraphQL client.
        """
        self._api_url = settings.HSL_ROUTING_API_URL
        self._subscription_key = settings.HSL_SUBSCRIPTION_KEY
        self._client: Optional[Client] = None

    def _get_client(self) -> Client:
        """
        Get or create GraphQL client instance.
        """
        if self._client is None:
            transport = HTTPXAsyncTransport(
                url=f"{self._api_url}?digitransit-subscription-key={self._subscription_key}",
                timeout=30.0,
            )
            self._client = Client(
                transport=transport,
                fetch_schema_from_transport=False,
            )
        return self._client

    async def get_itinaries(
        self,
        origin: Coordinates,
        destination: Coordinates,
        earliest_departure: datetime = datetime.now(timezone.utc),
        first: int = 3,
    ) -> List[Itinerary]:
        """
        Fetch route itineraries between two locations using HSL API.

        Queries the HSL GraphQL API to get public transport routes with detailed
        information about legs, duration, distance, and transport modes.

        Args:
            origin: Coordinates of the starting point
            destination: Coordinates of the destination point
            earliestDeparture: Earliest departure time (defaults to now)
            first: Number of route alternatives to return (default: 3)

        Returns:
            List of Itinerary objects representing possible routes

        Raises:
            HTTPError: If the API request fails
            GraphQLError: If the GraphQL query is invalid
            ValueError: If coordinates are invalid
        """
        if earliest_departure.tzinfo is None:
            earliest_departure = earliest_departure.replace(tzinfo=timezone.utc)

        variables = {
            "originLat": origin.latitude,
            "originLon": origin.longitude,
            "destinationLat": destination.latitude,
            "destinationLon": destination.longitude,
            "first": first,
            "earliestDeparture": earliest_departure.isoformat(),
        }

        try:
            client = self._get_client()
            query = gql(ITINERARY_QUERY)

            result = await client.execute_async(query, variable_values=variables)

            return self._parse_itinaries(result)
        except TransportQueryError as e:
            logger.error("HSL API returned an error: %s", str(e))
            raise RoutingAPIError(f"HSL API error: {str(e)}") from e

        except TimeoutException as e:
            logger.error("Request to HSL API timed out")
            raise RoutingNetworkError("Request timed out") from e

        except HTTPError as e:
            logger.error("Network error while contacting HSL API: %s", str(e))
            raise RoutingNetworkError(f"Network error: {str(e)}") from e

        except (KeyError, ValueError, TypeError) as e:
            logger.error("Failed to parse HSL API response: %s", str(e))
            raise RoutingDataError(f"Invalid response data: {str(e)}") from e

        except Exception as e:
            logger.exception("Unexpected error in routing service")
            raise RoutingServiceError(f"Unexpected error: {str(e)}") from e

    def _parse_itinaries(self, data: Dict) -> List[Itinerary]:
        """
        Parse GraphQL response data into list of Itinerary objects.
        """
        itineraries: List[Itinerary] = []
        edges = data.get("planConnection", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            itineraries.append(self._parse_itinary(node))
        return itineraries

    def _parse_itinary(self, data: Dict) -> Itinerary:
        """
        Parse a single itinerary from GraphQL response data.
        """
        return Itinerary(
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
            duration=data["duration"],
            walk_distance=data["walkDistance"],
            walk_time=data["walkTime"],
            legs=[self._parse_leg(leg) for leg in data.get("legs", [])],
        )

    def _parse_leg(self, data: Dict) -> Leg:
        """
        Parse a single leg from GraphQL response data.
        """
        return Leg(
            mode=TransportMode(data["mode"]),
            start=datetime.fromisoformat(data["start"]["scheduledTime"]),
            end=datetime.fromisoformat(data["end"]["scheduledTime"]),
            duration=data["duration"],
            distance=data["distance"],
            from_place=Place(
                coordinates=Coordinates(
                    latitude=data["from"]["lat"], longitude=data["from"]["lon"]
                ),
                name=data["from"]["name"],
            ),
            to_place=Place(
                coordinates=Coordinates(latitude=data["to"]["lat"], longitude=data["to"]["lon"]),
                name=data["to"]["name"],
            ),
            route=self._parse_route(data["route"]) if data.get("route") else None,
        )

    def _parse_route(self, data: Dict) -> Route:
        """
        Parse route information from GraphQL response data.
        """
        return Route(
            short_name=data["shortName"],
            long_name=data["longName"],
            description=data.get("desc"),
        )

    async def close(self):
        """
        Close the GraphQL client and cleanup resources.

        TODO: Implement cleanup logic
        """
        if self._client is not None:
            await self._client.close_async()
            self._client = None


# Singleton instance for dependency injection
routing_service = RoutingService()
