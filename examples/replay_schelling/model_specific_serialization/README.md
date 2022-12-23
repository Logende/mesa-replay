# Model Specific Serialization
This example is based on the example in `combined_simulate_and_replay_server` but additionally implements custom serialization and deserialization of the model state. 
For smaller or medium-sized models this might not matter, however, for models with a huge state it does: by default, Mesa-Replay caches everything of a models state, making 100% accurate replay possible. 
This does come at the cost of requiring more cache size than usually necessary. 
As Mesa-Replay aims to remain simple and generic, plus the question of "What data from my model is really necessary for replay?" is mostly model-specific, optimized serialization is up to the user of Mesa-Replay. 
For some models, this can decrease cache size (in memory and on file system) drastically.