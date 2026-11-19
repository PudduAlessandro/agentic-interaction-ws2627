import json
import os
import sys
import time

from .logging import log_event, log_error
from .tools import TOOLS, TOOL_FUNCTIONS, normalize_date
from .config import load_settings, SYSTEM_PROMPT

import requests
from openai import OpenAI

class StepLimitExceeded(RuntimeError):
    """Raised when an agent run reaches its maximum number of tool calls."""

settings = load_settings()

# Function to run step loop for tool calls, logging each step and handling errors
def execute_tool_calls(tool_calls, messages,step_count) -> int:
    """Execute every requested date lookup and append each result."""
    for tool_call in tool_calls:
        if step_count >= settings.max_steps:
            error = StepLimitExceeded(f"Maximum number of steps ({settings.max_steps}) reached.")
            log_error(time.perf_counter(), settings.model,"agent",{"step": step_count, "max_steps": settings.max_steps}, error)
            raise error
        step_count += 1

        tool_name = tool_call.function.name
        tool_function = TOOL_FUNCTIONS.get(tool_name)

        if tool_function is None:
            raise RuntimeError(f"Unsupported tool: {tool_name}")

        arguments = json.loads(tool_call.function.arguments)

        if tool_name == "get_appointments":
            arguments["appointment_date"] = normalize_date(
                arguments["appointment_date"]
            )

        tool_args = {
            **arguments,
            "step": step_count,
        }

        log_event( "tool_call", settings.model, time.perf_counter(), tool_name,tool_args)
        try:
            result = tool_function(**arguments)
        except Exception as error:
            log_error(time.perf_counter(), settings.model, tool_name, tool_args, error)
            if isinstance(error, requests.RequestException):
                raise RuntimeError(f"{tool_name} request failed: {error}") from error
            raise
        log_event("tool_result", settings.model, time.perf_counter(), tool_name, tool_args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_name,
            "content": result,
        })
    return step_count


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m agent '<question>'", file=sys.stderr)
        return 2


    # Read prompt from user input in command line
    prompt = " ".join(sys.argv[1:]).strip()
    model = os.environ.get("MODEL", "")
    log_event("user_task", settings.model, time.perf_counter(),"agent",{"prompt": prompt},)

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    messages = [
        {"role": "system","content": SYSTEM_PROMPT,},
        {"role": "user","content": prompt},
    ]

    model_args = {"message_count": len(messages), "has_tools": True}
    log_event("tool_call", settings.model, time.perf_counter(),"chat.completions.create", model_args)

    # Attempt to build the client with model, tools and system prompt
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
        )
    except Exception as error:
        log_error(time.perf_counter(), settings.model, "chat.completions.create", model_args, error)
        raise
    log_event("tool_result", settings.model, time.perf_counter(),"chat.completions.create", model_args)

    assistant_message = response.choices[0].message
    messages.append(assistant_message)

    # If there was no date found, there was no reason to call a tool
    if not assistant_message.tool_calls:
        print(assistant_message.content or "Please provide a date in YYYY-MM-DD format.")
        return 0

    step_count = execute_tool_calls(
        assistant_message.tool_calls,
        messages,
        0,
    )

    # If there were no tool calls, we're done
    while True:
        started_at = time.perf_counter()
        final_args = {"message_count": len(messages), "has_tools": True}
        log_event("tool_call",settings.model, time.perf_counter(),"chat.completions.create", final_args)

        try:
            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
            )

        except Exception as error:
            log_error(time.perf_counter(),settings.model,"chat.completions.create", final_args, error)
            raise
        log_event("tool_result",settings.model, time.perf_counter(),"chat.completions.create", final_args)

        final_message = final_response.choices[0].message
        messages.append(final_message)
        if not final_message.tool_calls:
            final_content = final_message.content
            break
        step_count = execute_tool_calls(
            final_message.tool_calls,
            messages,
            step_count,
        )
    log_event("final", settings.model, time.perf_counter(),"agent",{"response_length": len(final_content or "")})
    print(final_content)
    return 0

# TODO: Maybe rework the entire thing to be better structured. Tools in own file, own config file, etc. (maybe look how others did it for inspiration)
if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)