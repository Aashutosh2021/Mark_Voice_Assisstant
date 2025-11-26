import requests
import json

def get_weather_forecast(api_key, city):
    """
    Retrieves the weather forecast for a given city.

    Args:
        api_key (str): The API key for the OpenWeatherMap API.
        city (str): The city for which to retrieve the weather forecast.

    Returns:
        dict: A dictionary containing the weather forecast data.
    """
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

    return response.json()


def print_weather_forecast(weather_data):
    """
    Prints the weather forecast data in a human-readable format.

    Args:
        weather_data (dict): A dictionary containing the weather forecast data.
    """
    if weather_data is None:
        print("No weather data available.")
        return

    print("Weather Forecast:")
    for forecast in weather_data["list"]:
        date = forecast["dt_txt"]
        temperature = forecast["main"]["temp"]
        feels_like = forecast["main"]["feels_like"]
        humidity = forecast["main"]["humidity"]
        weather_description = forecast["weather"][0]["description"]

        print(f"Date: {date}")
        print(f"Temperature: {temperature}°C")
        print(f"Feels like: {feels_like}°C")
        print(f"Humidity: {humidity}%")
        print(f"Weather: {weather_description}")
        print("------------------------")


def main():
    api_key = "YOUR_OPENWEATHERMAP_API_KEY"
    city = "London"

    weather_data = get_weather_forecast(api_key, city)
    print_weather_forecast(weather_data)


if __name__ == "__main__":
    main()