from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

MODEL = "gemini-3.8-flash"


root_agent = Agent(
    # Keep in sync with agents-cli-manifest.yaml: agents-cli derives this name
    # from the project `name:` recorded there, and telemetry reports it as
    # gen_ai.agent.name. Renaming the agent only here makes the two disagree,
    # and anything selecting traces by name stops finding this agent's.
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a helpful AI assistant. When given extracted invoice and purchase "
        "order JSON for comparison, act as an auditor: compare only fields present "
        "in the supplied data, identify mismatches with the field name and both "
        "values, explain their practical significance briefly, and distinguish "
        "missing information from a confirmed discrepancy. Never invent values. "
        "If no discrepancies are found in the available fields, say so."
    ),
)

app = App(
    root_agent=root_agent,
    name="app",
)
