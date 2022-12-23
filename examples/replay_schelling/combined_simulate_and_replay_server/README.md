# Combined Simulate and Replay Server
This example implements `CachableSchelling` in `cachablemodel.py` with the additional `replay` parameter, next to the regular Schelling model parameters. 
As a result the property of whether to simulate or replay becomes a simulation model parameter. 
This parameter we add to the `model_params` variable, which we hand over to our server in `run.py`

The result is that when running the server, the replay/simulate mode can be toggled using an interactive checkbox in the web view.