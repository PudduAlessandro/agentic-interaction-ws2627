import json
import os
from datetime import datetime

import requests

current_date = datetime.now().astimezone().date().isoformat()

TOOLS = [
    {
            "type": "function",
            "function": {
                "name": "get_appointments",
                "description": (
                    "Retrieve all calendar appointments for one specific date. "
                    f"Today's date is the {current_date}. Should the user ask for appointments regarding dates in relation to today, attempt to calculate the date and call this tool with the correct date. "
                    "The date may use YYYY-MM-DD or European DD.MM.YYYY format. "
                    "For multiple dates, create one tool call per date."
                    "Always return information about the requested appointments in the same language the user asked the question in."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_date": {
                            "type": "string",
                            "description": (
                                "Date to query in YYYY-MM-DD or DD.MM.YYYY format."
                            ),
                        }
                    },
                    "required": ["appointment_date"],
                    "additionalProperties": False,
                },
            },
        },{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": (
                    "Retrieve the weather data for a given city on a specific date."
                    "If the city name is written in a language other than German, translate it to German, make it lowercase and convert any umlauts to their respective letter combinations (ä -> ae, ö -> oe, ü -> ue)."
                    "If no specific city is mentioned, assume that the user is located in Ulm."
                    "Always return information about the requested weather in the same language the user asked the question in."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": (
                                "City to request weather data about"
                            ),
                        },"date": {
                            "type": "string",
                            "description": (
                                "Date for which to request weather data"
                            ),
                        }
                    },
                    "required": ["city", "date"],
                    "additionalProperties": False,
                },
            },
        },{
            "type": "function",
            "function": {
                "name": "get_connections",
                "description": (
                    "Retrieve train connections from one city to another"
                    "Connection data can include departure times, train numbers/names and cost per ride, responses about connections should contain all these details."
                    "If any city name is written in a language other than German, translate it to German, make it lowercase and convert any umlauts to their respective letter combinations (ä -> ae, ö -> oe, ü -> ue)."
                    "If city names are already written in German, make them lowercase and convert any umlauts to their respective letter combinations (ä -> ae, ö -> oe, ü -> ue)."
                    "If the user only asks about going somewhere without mentioning a city to start from, assume they are located in Ulm."
                    "Do not invent any data regarding connections and only use the data you receive"
                    "Always return information about the requested connection in the same language the user asked the question in. Should the retrieved data be in German, translate it into the language the user asked the question in."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to_city": {
                            "type": "string",
                            "description": (
                                "Name of the city the user wants to travel to."
                                "If the city name is written in a language other than German, translate it to German, make it lowercase and convert any umlauts to their respective letter combinations (ä -> ae, ö -> oe, ü -> ue)."
                                "If the city name is already written in German, make it lowercase and convert any umlauts to their respective letter combinations (ä -> ae, ö -> oe, ü -> ue)."
                            ),
                        },
                        "from_city": {
                            "type": "string",
                            "description": (
                                "Name of the city the user wants start travelling from."
                                "If no start city is mentioned, assume the user is located in Ulm."
                                "If the city name is written in a language other than German, translate it to German, make it lowercase and convert any umlauts to their respective letter combinations (ä -> ae, ö -> oe, ü -> ue)."
                                "If the city name is already written in German, make it lowercase and convert any umlauts to their respective letter combinations (ä -> ae, ö -> oe, ü -> ue)."
                            ),
                        },
                        "date": {
                            "type": "string",
                            "description": (
                                "The date for which to request connection data in YYYY-MM-DD or DD.MM.YYYY format."
                            ),
                        },
                    },
                    "required": ["to_city", "date"],
                    "additionalProperties": False,
                },
            },
        },
    ]


def normalize_date(date: str) -> str:
    """
    Formats and returns the entered date from user prompt to YYYY-MM-DD format for calendar endpoint use
    :return: Date string in YYYY-MM-DD format
    """
    date = date.strip()
    for date_format in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date, date_format).date().isoformat()
        except ValueError:
            continue

    raise ValueError(
        f"Invalid date {date!r}! Expected date in a valid date format"
    )


def get_appointments(appointment_date: str) -> str:
    """
    Agent tool function to retrieve all calendar appointments for a single date.
    :param appointment_date: Date for which to retrieve appointments.
    :return: JSON string containing the appointments.
    """
    url = os.environ.get("DATA_BASE_URL") + f"/calendar/{appointment_date}.json"
    response = requests.get(url, timeout=15)

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError("The calendar returned a non-JSON response.") from error

    return json.dumps(data, ensure_ascii=False)


def get_weather(city: str, date: str) -> str:
    """
    Get the weather of a city from an API endpoint
    :param city: City of which to get the weather for
    :param date: Date for which to get the weather for
    :return: Gathered weather data in json format
    """

    url = os.environ.get("DATA_BASE_URL") + f"/weather/{city}/{date}.json"
    response = requests.get(url, timeout=15)

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError("The weather endpoint was unavailable or returned a non-JSON response") from error

    return json.dumps(data, ensure_ascii=False)


def get_connection(date: str, to_city: str, from_city="ulm",) -> str:
    """
    Get the train connections from one city to another on a specific date
    :param date: Date for which to get the train connections
    :param to_city: City the user wants to travel to
    :param from_city: City the user wants to travel from, defaults to Ulm if not specified
    :return:
    """
    url = os.environ.get("DATA_BASE_URL") + f"/transit/{from_city}/{to_city}/{date}.json"
    response = requests.get(url, timeout=15)

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError("The calendar returned a non-JSON response.") from error

    return json.dumps(data, ensure_ascii=False)

TOOL_FUNCTIONS = {
    "get_appointments": get_appointments,
    "get_weather": get_weather,
    "get_connections": get_connection,
}