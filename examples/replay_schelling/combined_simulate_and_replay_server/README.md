# Combined Simulate and Replay Server
This example puts the Schelling model inside a CachableModel wrapper that we name `CachableSchelling`.
From the outside perspective, it behaves the same way as the original Schelling model, but additionally supports caching.
It implements `CachableSchelling` in `cachablemodel.py` with the additional `replay` parameter, next to the regular Schelling model parameters. 
As a result the property of whether to simulate or replay becomes a simulation model parameter. 
This parameter must be added to the `model_params` variable, which is handed over to the server in `run.py`.

The result is that when running the server, the replay/simulate mode can be toggled using an interactive checkbox in the web view.