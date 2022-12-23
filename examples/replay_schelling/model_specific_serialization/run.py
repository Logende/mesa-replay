import mesa

from examples.replay_schelling.server import canvas_element, get_happy_agents, happy_chart, model_params
from cachablemodel import CachableSchelling

# As 'replay' is a simulation model parameter in this example, we need to make it available here
model_params["replay"] = mesa.visualization.Checkbox("Replay last run?", False)

server = mesa.visualization.ModularServer(
    # Note that Schelling was replaced by CachableSchelling here
    CachableSchelling,
    [canvas_element, get_happy_agents, happy_chart],
    "Schelling",
    model_params,
)

server.launch()
