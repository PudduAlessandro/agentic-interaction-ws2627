import json
from pathlib import Path

WRITE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_appointment",
            "description": (
                "Create a new appointment in the users calendar."
                "A calendar appointment requires a date, start time, end time and title. Location and details are optional."
                "Locations can be either a city, address or a room number. If a location is provided, it should be included in the appointment."
                "Details can be any additional information about the appointment. If details are provided, they should be included in the appointment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": (
                            "The date for which to create the appointment in YYYY-MM-DD format."
                        ),
                    },
                    "start_time": {
                        "type": "string",
                        "description": (
                            "The start time for the appointment in HH:MM format."
                        ),
                    },
                    "end_time": {
                        "type": "string",
                        "description": (
                            "The end time for the appointment in HH:MM format."
                        ),
                    },
                    "title": {
                        "type": "string",
                        "description": (
                            "The title of the appointment."
                        ),
                    },
                    "location": {
                        "type": "string",
                        "description": (
                            "The location of the appointment. This can be a city, address or a room number."
                        ),
                    },
                    "details": {
                        "type": "string",
                        "description": (
                            "Any additional details about the appointment."
                        ),
                    },
                },
                "required": ["date", "start_time", "end_time", "title"],
                "additionalProperties": False,
            },
        },
    },
    ]

def preview_appointment(date: str, start_time: str, end_time: str, title: str, location="", details="") -> str:
    """
    Shows how a possible new appointment would look before writing it.
    :param date: Date of the appointment in YYYY-MM-DD format
    :param start_time: Start time of the appointment in HH:MM format
    :param end_time: End time of the appointment in HH:MM format
    :param title: Title of the appointment
    :param location: Location/Room of the appointment
    :param details: Additional details about the appointment
    :return: Preview of the proposed appointment.
    """
    lines = [
        "Proposed appointment:",
        f"Date: {date}",
        f"Time: {start_time}–{end_time}",
        f"Title: {title}",
    ]
    if location:
        lines.append(f"Location: {location}")
    if details:
        lines.append(f"Details: {details}")
    return "\n".join(lines)

def create_appointment(date: str, start_time: str, end_time: str, title: str, location="", details="") -> str:
    """
    Creates a new appointment.
    :param date: Date of the appointment in YYYY-MM-DD format
    :param start_time: Start time of the appointment in HH:MM format
    :param end_time: End time of the appointment in HH:MM format
    :param title: Title of the appointment
    :param location: Location/Room of the appointment
    :param details: Additional details about the appointment
    :return: Returns whether the appointment was successfully created
    """
    calendar_dir = Path(__file__).with_name("var")
    file_path = calendar_dir / "calendar.jsonl"

    record = {
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "title": title,
    }

    if location:
        record["location"] = location
    if details:
        record["details"] = details

    try:
        calendar_dir.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as calendar_file:
            calendar_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as error:
        return f"Error creating appointment: {error}"

    return f"Appointment with data {record} created successfully."

WRITE_TOOL_FUNCTIONS = {
    "create_appointment": create_appointment,
}

WRITE_TOOL_HANDLERS = {
    "create_appointment": {
        "direct": create_appointment,
        "preview": preview_appointment,
    },
}