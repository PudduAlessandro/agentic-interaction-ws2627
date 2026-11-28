import json
import os
import sys
import time

from .logging import log_event, log_error
from .read_tools import READ_TOOLS, READ_TOOL_FUNCTIONS, normalize_date
from .write_tools import WRITE_TOOLS, WRITE_TOOL_HANDLERS
from .config import load_settings, SYSTEM_PROMPT, Condition

from openai import OpenAI

class StepLimitExceeded(RuntimeError):
    """Raised when an agent run reaches its maximum number of tool calls."""

settings = load_settings()

AVAILABLE_TOOLS = READ_TOOLS + WRITE_TOOLS

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
        tool_args = {"step": step_count}

        try:
            arguments = json.loads(tool_call.function.arguments)
            tool_args = {
                **arguments,
                "step": step_count,
            }
            log_event("tool_call", settings.model, time.perf_counter(), tool_name, tool_args)

            write_handler = WRITE_TOOL_HANDLERS.get(tool_name)
            if write_handler is not None:
                if settings.condition == Condition.PREVIEW:
                    preview = write_handler["preview"](**arguments)
                    print(preview)
                    confirmed = input("Proceed with this change? [y/N]: ").strip().lower()
                    if confirmed not in {"y", "yes"}:
                        result = "Denied by user; no changes were made."
                    else:
                        result = write_handler["direct"](**arguments)
                else:
                    result = write_handler["direct"](**arguments)
            else:
                tool_function = READ_TOOL_FUNCTIONS.get(tool_name)
                if tool_function is None:
                    raise RuntimeError(f"Unsupported tool: {tool_name}")

                if tool_name == "get_appointments":
                    arguments["appointment_date"] = normalize_date(
                        arguments["appointment_date"]
                    )

                result = tool_function(
                    **arguments,
                    data_base_url=settings.data_base_url,
                )
        except Exception as error:
            log_error(time.perf_counter(), settings.model, tool_name, tool_args, error)
            if tool_name in WRITE_TOOL_HANDLERS:
                result = f"Unable to execute {tool_name}: {error}"
            else:
                result = (
                    f"Unable to retrieve data for {tool_name}. "
                    "The external service failed or returned an error."
                )
        else:
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
            tools=AVAILABLE_TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
        )
    except Exception as error:
        log_error(time.perf_counter(), settings.model, "chat.completions.create", model_args, error)
        raise
    log_event("tool_result", settings.model, time.perf_counter(),"chat.completions.create", model_args)

    assistant_message = response.choices[0].message
    messages.append(assistant_message)

    # If there was not enough information in the prompt to determine a tool to call, return an error message
    if not assistant_message.tool_calls:
        print(assistant_message.content or "I was unable to determine which tool to call. Please provide a valid date or specify a destination to get train connections or weather data about.")
        return 0

    step_count = execute_tool_calls(
        assistant_message.tool_calls,
        messages,
        0,
    )

    # If there were no tool calls, we're done
    while True:
        final_args = {"message_count": len(messages), "has_tools": True}
        log_event("tool_call",settings.model, time.perf_counter(),"chat.completions.create", final_args)

        try:
            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=AVAILABLE_TOOLS,
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


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)