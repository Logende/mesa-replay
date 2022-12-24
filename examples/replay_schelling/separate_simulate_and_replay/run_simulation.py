import mesa

from examples.replay_schelling.server import (
    canvas_element,
    get_happy_agents,
    happy_chart,
    model_params,
)
from cacheablemodel import CacheableSchellingSimulate


server = mesa.visualization.ModularServer(
    # Note that Schelling was replaced by CacheableSchellingSimulate here
    CacheableSchellingSimulate,
    [canvas_element, get_happy_agents, happy_chart],
    "Schelling",
    model_params,
)

server.launch()
