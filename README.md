# Mesa-Replay
Enables caching simulations of mesa models, persisting them on the file system and replaying them later.

## What is Mesa?

[Mesa](https://github.com/projectmesa/mesa) is a agent-based simulation framework written in Python.
> Mesa allows users to quickly create agent-based models using built-in core
> components (such as spatial grids and agent schedulers) or customized implementations;
> visualize them using a browser-based interface; and analyze their results using Python's
> data analysis tools. Its goal is to be the Python 3-based alternative to NetLogo,
> Repast, or MASON.

![A Mesa implementation of the Schelling segregation model,
being visualized in a browser window and analyzed in a Jupyter notebook.](figs/Mesa_Screenshot.png)

*A Mesa implementation of the Schelling segregation model,
being visualized in a browser window and analyzed in a Jupyter notebook*

> **Agent-based models** are computer simulations involving multiple entities (the agents)
> acting and interacting with one another based on their programmed behavior.
> Agents can be used to represent living cells, animals, individual humans,
> even entire organizations or abstract entities.
> Sometimes, we may have an understanding of how the individual components
> of a system behave, and want to see what system-level behaviors and
> effects emerge from their interaction. Other times, we may have a good idea
> of how the system overall behaves, and want to figure out what individual behaviors
> explain it. Or we may want to see how to get agents to cooperate or compete most
> effectively. Or we may just want to build a cool toy with colorful little dots moving around.

For more information and an example of how to use Mesa, see <https://mesa.readthedocs.io/en/main/overview.html>.

## What is Mesa-Replay?

Depending on the complexity of a simulation model, the algorithms being used and the hardware, it can take many hours or even days for a simulation to run. 
Once a simulation run is finished and the application is closed, typically some chosen generated data is persisted, but everything else is gone. 
Unlike with a video, there is no way of going back within the simulation or replaying a simulation. 
You wrote an impressive COVID simulation that is quite accurate but takes over 10 hours to run? 
It is inconvenient for you to demonstrate or play your simulation live because it takes so much time?

Mesa-Replay addresses and solves those issues by enabling you to **cache your entire simulation run, persist the cached "run" on your file system and replay it later**.

**Use-cases**:

- You have an interesting simulation run/result that you want to share with your peers
- Let the simulation take its time but replay everything as fast as you want, making demonstrations easier
- Even continue a previous simulation run that was stopped and persisted at some point

Mesa-Replay is developed with the goal of being **simple**, **generic** and **accessible**.

# Installation

To locally install Mesa-Replay as a pip module, install in ['editable' mode](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs):
```bash
pip install -e .
```

# How to Use

For usage examples, see [here](https://github.com/Logende/mesa-replay/tree/main/examples).

The [test files](https://github.com/Logende/mesa-replay/tree/main/tests) (they have extensive descriptions) also illustrate the functionality of Mesa-Replay. To test them, run:

```bash
python -m unittest tests/test_*
```
