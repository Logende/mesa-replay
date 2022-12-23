from examples.replay_schelling.model import Schelling
from mesa_replay import CachableModel, CacheState


class CachableSchellingSimulate(CachableModel):
    def __init__(self, width=20, height=20, density=0.8, minority_pc=0.2, homophily=3):
        actual_model = Schelling(width, height, density, minority_pc, homophily)
        super().__init__(actual_model, cache_file_path="my_cache_file_path.cache", cache_state=CacheState.WRITE)


class CachableSchellingReplay(CachableModel):
    def __init__(self, width=20, height=20, density=0.8, minority_pc=0.2, homophily=3):
        actual_model = Schelling(width, height, density, minority_pc, homophily)
        super().__init__(actual_model, cache_file_path="my_cache_file_path.cache", cache_state=CacheState.READ)
