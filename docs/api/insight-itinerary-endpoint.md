# Insight/Itinerary Endpoint Documentation

## Overview

The `/api/v1/insight/itinerary` endpoint provides AI-generated insights and descriptions for complete journey itineraries. This endpoint analyzes the entire journey, including all legs and transportation modes, to generate:
- An overall description of the itinerary
- Specific insights for each individual leg of the journey

## Endpoint

```
POST /api/v1/insight/itinerary
```

## Request Schema

### ItineraryInsightRequest

The request body contains the complete itinerary information along with optional user preferences.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | `string` | Yes | Start time in ISO 8601 format (e.g., "2025-10-14T10:00:00Z") |
| `end` | `string` | Yes | End time in ISO 8601 format (e.g., "2025-10-14T11:30:00Z") |
| `duration` | `integer` | Yes | Total duration in seconds |
| `walk_distance` | `float` | Yes | Total walking distance in meters |
| `walk_time` | `integer` | Yes | Total walking time in seconds |
| `legs` | `List[LegInsightData]` | Yes | List of journey legs (see below) |
| `user_preferences` | `List[string]` | No | Optional list of user preferences to consider for insights |

### LegInsightData

Each leg represents a segment of the journey with a specific transport mode.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | `string` | Yes | Transport mode (e.g., "WALK", "BUS", "TRAM", "TRAIN", "SUBWAY") |
| `duration` | `integer` | Yes | Duration of this leg in seconds |
| `distance` | `float` | Yes | Distance of this leg in meters |
| `from_place` | `string` | Yes | Name of the starting place (empty string if not available) |
| `to_place` | `string` | Yes | Name of the destination place (empty string if not available) |
| `route` | `RouteInsightData \| null` | No | Route information if applicable (null for walking legs) |

### RouteInsightData

Route information for public transportation legs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `short_name` | `string` | Yes | Short name of the route (e.g., "550", "M1", "T2") |
| `long_name` | `string` | Yes | Long/full name of the route (e.g., "Helsinki - Espoo") |

## Response Schema

### ItineraryInsightResponse

The response contains AI-generated insights for the entire itinerary and individual legs.

| Field | Type | Description |
|-------|------|-------------|
| `ai_insight` | `string \| null` | AI-generated insight about the overall itinerary |
| `ai_insights` | `List[string \| null]` | List of AI-generated insights for each leg. Each insight corresponds to a leg in the request (by index). May be null for individual legs if no specific insight is available. |

## Example Request

```json
{
  "start": "2025-10-14T10:00:00Z",
  "end": "2025-10-14T11:30:00Z",
  "duration": 5400,
  "walk_distance": 1200.5,
  "walk_time": 900,
  "legs": [
    {
      "mode": "WALK",
      "duration": 600,
      "distance": 500.0,
      "from_place": "Home",
      "to_place": "Main Street Bus Stop",
      "route": null
    },
    {
      "mode": "BUS",
      "duration": 1800,
      "distance": 10000.0,
      "from_place": "Main Street Bus Stop",
      "to_place": "Central Station",
      "route": {
        "short_name": "550",
        "long_name": "Helsinki - Espoo Express"
      }
    },
    {
      "mode": "WALK",
      "duration": 300,
      "distance": 250.0,
      "from_place": "Central Station",
      "to_place": "Office Building",
      "route": null
    }
  ],
  "user_preferences": [
    "Prefer routes with less walking",
    "Avoid crowded buses during rush hour"
  ]
}
```

## Example Response

```json
{
  "ai_insight": "This 90-minute commute from home to your office combines walking and public transit. The journey starts with a short 10-minute walk to the bus stop, followed by a 30-minute express bus ride on route 550, and concludes with a brief 5-minute walk to your destination. The total walking distance is approximately 1.2 km, which is moderate and provides some physical activity during your commute.",
  "ai_insights": [
    "A short 500-meter walk to the bus stop. Consider leaving a few minutes early during rainy weather.",
    "The 550 express bus provides a direct connection and typically has good frequency during peak hours. However, it may be crowded during morning rush hour based on your preferences.",
    "A brief walk from the station to your office, perfect for a mental transition before starting work."
  ]
}
```

## Usage Notes

1. **Timestamp Format**: All timestamps must be in ISO 8601 format with timezone information.

2. **Leg Order**: The order of legs in the request is important. The AI insights in the response will correspond to legs by their index position.

3. **Walking Legs**: Walking legs should have `route` set to `null`.

4. **User Preferences**: Including user preferences helps the AI tailor insights to user needs (e.g., accessibility requirements, comfort preferences).

5. **Error Handling**: If the AI service is unavailable or returns an error, the endpoint may return empty or null insights gracefully.

6. **Transport Modes**: Common transport modes include:
   - `WALK` - Walking
   - `BUS` - Bus
   - `TRAM` - Tram/Streetcar
   - `TRAIN` - Train
   - `SUBWAY` - Subway/Metro
   - `FERRY` - Ferry

## Integration Example

### Python (using the backend service)

```python
from app.services.ai_agents_service import ai_agents_service
from app.schemas.itinary import Itinerary

async def enrich_itinerary_with_ai(itinerary: Itinerary, user_preferences: list = None):
    """
    Enrich an itinerary object with AI-generated insights.
    
    Args:
        itinerary: The itinerary object to enrich
        user_preferences: Optional list of user preference strings
    
    Returns:
        None - modifies the itinerary object in place
    """
    await ai_agents_service.get_itinerary_insight(itinerary, user_preferences)
    
    # After this call:
    # - itinerary.ai_insight will contain the overall insight
    # - each leg.ai_insight will contain leg-specific insights
```

### cURL Example

```bash
curl -X POST "https://api.example.com/api/v1/insight/itinerary" \
  -H "Content-Type: application/json" \
  -d '{
    "start": "2025-10-14T10:00:00Z",
    "end": "2025-10-14T11:30:00Z",
    "duration": 5400,
    "walk_distance": 1200.5,
    "walk_time": 900,
    "legs": [
      {
        "mode": "WALK",
        "duration": 600,
        "distance": 500.0,
        "from_place": "Home",
        "to_place": "Bus Stop",
        "route": null
      }
    ],
    "user_preferences": ["Prefer less walking"]
  }'
```

## Schema Implementation

The schemas are implemented in `app/schemas/ai_agents.py` using Pydantic models:

- `ItineraryInsightRequest` - Request model with validation
- `ItineraryInsightResponse` - Response model 
- `LegInsightData` - Individual leg information
- `RouteInsightData` - Route details for public transport legs

All models include field validation and clear descriptions for API documentation and type checking.
