"""Exercise 1 (slides 33-41): weather bot with LangGraph, no LLM.

Fill in the TODOs below, following the slides.
"""

from typing import Literal, Optional, TypedDict
from langgraph.graph import StateGraph, END, START

# TODO: define State (TypedDict: message, location, forecast, response)

# TODO: data helpers - extract_location, is_ambiguous, fetch_weather_data,
# generate_location_clarification, format_weather_response

# TODO: nodes - parse_message, get_forecast, clarify_location, generate_response

# TODO: conditional edge - check_location(state) -> "valid" | "invalid" | "ambiguous"

# TODO: build the graph (add_node / add_edge / add_conditional_edges), compile as `app`

# TODO: visualize (graph.png) and run:
#   app.invoke({"message": "What is the weather in seoul"})
