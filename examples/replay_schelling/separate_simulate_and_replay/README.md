# Separate Simulate and Replay
This example implements `CachableSchellingSimulate` and `CachableSchellingReplay` separately, in `cachablemodel.py` .

The result is that before starting a new run, it can be decided whether to simulate a regular run, which is being cached (`run_simulation.py`), or to replay an existing run (`run_replay.py`). This is likely the common use-case.

Note that this examples has a hardcoded `cache_file` path. Whenever a new simulation run with caching started, the previous cache will be overwritten. If the intention is to create different files that can be replayed later, of course, the cache_file path needs to be adjusted accordingly every time.