"""
Weather service for fetching forecast data.
"""

from datetime import date, datetime

import httpx
import structlog

logger = structlog.get_logger(__name__)


class WeatherService:
    """Service for fetching weather data from Open-Meteo API."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @classmethod
    def get_forecast(
        cls,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        timezone: str = "auto",
    ) -> list[dict] | None:
        """
        Fetch weather forecast for a location and date range.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Forecast start date
            end_date: Forecast end date
            timezone: Timezone for temperature times (default: auto)

        Returns:
            List of daily forecast dicts with date, high, low temps, or None if error
        """
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone": timezone,
                "temperature_unit": "fahrenheit",
            }

            logger.info(
                "fetching_weather_forecast",
                latitude=latitude,
                longitude=longitude,
                start_date=str(start_date),
                end_date=str(end_date),
            )

            response = httpx.get(cls.BASE_URL, params=params, timeout=10.0)
            response.raise_for_status()

            data = response.json()

            # Parse response into list of daily forecasts
            forecasts = []
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            weather_codes = daily.get("weathercode", [])
            precipitation_probs = daily.get("precipitation_probability_max", [])

            for i, forecast_date in enumerate(dates):
                # Convert string date to date object for Django template filter
                date_obj = (
                    datetime.strptime(forecast_date, "%Y-%m-%d").date()
                    if isinstance(forecast_date, str)
                    else forecast_date
                )

                weather_code = weather_codes[i] if i < len(weather_codes) else None
                precip_prob = precipitation_probs[i] if i < len(precipitation_probs) else None

                forecasts.append(
                    {
                        "date": date_obj,
                        "date_str": forecast_date,  # Keep string version for display
                        "high": round(max_temps[i]) if i < len(max_temps) else None,
                        "low": round(min_temps[i]) if i < len(min_temps) else None,
                        "weather_code": weather_code,
                        "weather_icon": cls._get_weather_icon(weather_code, precip_prob),
                        "precipitation_chance": precip_prob,
                    }
                )

            logger.info(
                "weather_forecast_success",
                forecast_count=len(forecasts),
                latitude=latitude,
                longitude=longitude,
            )

            return forecasts

        except httpx.HTTPError as e:
            logger.error(
                "weather_api_http_error", error=str(e), latitude=latitude, longitude=longitude
            )
            return None
        except Exception as e:
            logger.error(
                "weather_api_error",
                error=str(e),
                latitude=latitude,
                longitude=longitude,
                exc_info=True,
            )
            return None

    @staticmethod
    def _get_weather_icon(weather_code: int | None, precipitation_prob: int | None = None) -> str:
        """
        Get emoji icon for WMO weather code, considering precipitation probability.

        WMO Weather interpretation codes (WW):
        0: Clear sky
        1-3: Mainly clear, partly cloudy, overcast
        45-48: Fog
        51-57: Drizzle
        61-67: Rain
        71-77: Snow
        80-82: Rain showers
        85-86: Snow showers
        95-99: Thunderstorm

        Logic: If precipitation probability is low (<30%), prefer sunny/cloudy icons
        even if weather code suggests rain, since there's a low chance of it occurring.
        """
        if weather_code is None:
            return "❓"

        # Fog always shows fog icon (weather type, not precipitation)
        if 45 <= weather_code <= 48:
            return "🌫️"

        # Snow - always show if code indicates snow (winter weather)
        if 71 <= weather_code <= 77 or 85 <= weather_code <= 86:
            return "❄️" if precipitation_prob is None or precipitation_prob >= 30 else "🌨️"

        # Thunderstorm - always show if code indicates thunderstorm (severe weather)
        if weather_code >= 95:
            return "⛈️"

        # Rain/drizzle - consider precipitation probability
        if 51 <= weather_code <= 67 or 80 <= weather_code <= 82:
            # If low chance of rain, show partly cloudy instead
            if precipitation_prob is not None and precipitation_prob < 30:
                return "🌤️"
            # Moderate chance - show sun behind rain cloud
            elif precipitation_prob is not None and precipitation_prob < 60:
                return "🌦️"
            # High chance - show rain cloud
            else:
                return "🌧️"

        # Clear sky
        if weather_code == 0:
            return "☀️"

        # Partly cloudy/overcast
        if weather_code <= 3:
            return "🌤️"

        # Default fallback
        return "❓"
