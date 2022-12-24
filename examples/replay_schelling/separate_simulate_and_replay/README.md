# Separate Simulate and Replay
This example puts the Schelling model inside two CacheableModel wrappers that we name `CacheableSchellingSimulate` and `CacheableSchellingReplay`.
From the user's perspective, those behave the same way as the original Schelling model, but additionally support caching.
If we use `CacheableSchellingSimulate`, with every simulation run the state of every step will be written to the cache file.
If we use `CacheableSchellingReplay`, with every simulation run the state of every step will be read from the cache file.

The result is that before starting a new run, it can be decided whether to simulate a regular run, which is being cached (`run_simulation.py`), or to replay an existing run (`run_replay.py`). 
This is likely the common use-case.

Note that this examples has a hardcoded `cache_file` path. 
Whenever a new simulation run with caching is started, the previous cache will be overwritten. 
If the intention is to create different files that can be replayed later, of course, the cache_file path needs to be adjusted accordingly every time.