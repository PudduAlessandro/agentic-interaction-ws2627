# Agentic Interaction Exercise
Learning how to implement an AI agent that runs tools and completes tasks. This description will be expanded as more functions get implemented.

## Functions
The agent is currently able to retrieve information from a specified endpoint about the following:
- Calendar appointments for one or multiple dates at once
- Weather information for a given location on a given date
- List train connections between two locations for a specified day

## Setup & How to Run
1. Clone using `git clone https://github.com/PudduAlessandro/agentic-interaction-ws2627.git`
2. Install required packages using `pip install -r requirements.txt`
3. Create a .env file in the `/agent` directory with the following content:
```
OPENAI_BASE_URL=<Base URL to model endpoint>
MODEL=<Model name>
OPENAI_API_KEY=<Your API key>
DATA_BASE_URL=<Base URL to data endpoint>
```
4. Run the agent via CLI from the cloned directory using `python -m agent <prompt>`


This project is being created as part of the "Agentic Human-AI Interaction" course at Ulm University.