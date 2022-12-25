"""
A decorator that wraps the model class of mesa and extends it by caching functionality.

Core Objects: CacheableModel
"""
from pathlib import Path
from enum import Enum
from typing import Any, Callable

import dill
import gzip

from mesa_replay.model_state_stripper import strip_off_unneeded_data_from_model_dict

from mesa import Model


class CacheState(Enum):
    """When using 'RECORD', with every simulation step the actual simulation will be performed and the model state
    written to the cache (also called simulation mode).
    When using 'REPLAY', with every step the model state will be read from the cache (also called replay mode)."""

    RECORD = (1,)
    REPLAY = 2


def _write_cache_file(cache_file_path: Path, cache_data: list[Any]) -> None:
    """Default function for writing the given cache data to the cache file.
    Used by CacheableModel if not replaced by a custom write function.
    Uses dill to dump the data into the file.
    Uses gzip for compression."""
    with gzip.open(cache_file_path, "wb") as file:
        dill.dump(cache_data, file)


def _read_cache_file(cache_file_path: Path) -> list[Any]:
    """Default function for reading the cache data from the cache file.
    Used by CacheableModel if not replaced by a custom read function.
    Expects that gzip and dill have been used to write the file."""
    with gzip.open(cache_file_path, "rb") as file:
        return dill.load(file)


class CacheableModel:
    """Class that takes a model and writes its steps to a cache file or reads them from a cache file."""

    def __init__(
        self,
        model: Model,
        cache_file_path: str | Path,
        cache_state: CacheState,
        cache_step_rate: int = 1,
    ) -> None:
        """Create a new caching wrapper around an existing mesa model instance.

        Attributes:
            model: mesa model
            cache_file_path: cache file to write to or read from
            cache_state: whether to replay by reading from the cache or simulate and write to the cache
            cache_step_rate: only every n-th step is cached. If it is 1, every step is cached. If it is 2,
            only every second step is cached and so on. Increasing 'cache_step_rate' will reduce cache size and
            increase replay performance by skipping the steps inbetween every n-th step.
        """
        self.model = model
        self.cache_file_path = Path(cache_file_path)
        self._cache_state = cache_state
        self._cache_step_rate = cache_step_rate

        self.cache: list[Any] = []
        self.step_count: int = 0
        self.run_finished = False

        if cache_state is CacheState.REPLAY:
            self._read_cache_file()
            # init the model at same state as cached model
            self._step_read_from_cache()

        elif cache_state is CacheState.RECORD:
            # store initial state of model in cache
            self._step_write_to_cache()

    def _serialize_state(self) -> Any:
        """Serialize the model state.
        Can be overwritten to write just parts of the state or other custom behavior.
        Needs to remain compatible with '_deserialize_state'.

        Note that for large model states, it might make sense to add compression during the serialization.
        That way the size of the cache in memory can be reduced. Additionally, while, by default, the resulting output
        cache file is compressed too (see '_write_cache_file'), this is not the case, when using other file handling
        behavior, such as writing to a buffered file stream during every step (see 'StreamingCacheableModel'). For such
        use-cases, a way to reduce the size of the resulting output cache file is to compress the individual steps. That
        way, for example, reading the cache from the file stream step by step remains possible, without having to
        load the complete cache into memory. This is not possible, when the complete output file is compressed.
        """
        stripped_dict_model = strip_off_unneeded_data_from_model_dict(
            self.model.__dict__
        )
        return dill.dumps(stripped_dict_model)

    def _deserialize_state(self, state: Any) -> None:
        """Deserialize the model state from the given input.
        Can be overwritten to load just parts of the state, decompress data, or other custom behavior.
        Needs to remain compatible with '_serialize_state'.
        """
        self.model.__dict__ = dill.loads(state)

    def _write_cache_file(self) -> None:
        """Write the cache from memory to 'cache_file_path'.
        Can be overwritten to, for example, use a different file format or compression or destination.
        Needs to remain compatible with '_read_cache_file'.
        """
        _write_cache_file(self.cache_file_path, self.cache)
        print("Wrote CacheableModel cache file to " + str(self.cache_file_path))

    def _read_cache_file(self) -> None:
        """Read the cache from 'cache_file_path' into memory.
        Can be overwritten to, for example, use a different file format or compression or location.
        Needs to remain compatible with '_write_cache_file'
        """
        self.cache = _read_cache_file(self.cache_file_path)

    def run_model(self) -> None:
        """Run the model until the end condition is reached."""
        # Right now if someone has a custom run_model function, they need to overwrite this function too.
        # That is because if they would use their own 'run_model()' function, they would access also their own 'step()'
        # function and not the outer level CacheableModel 'step()' function.
        while self.model.running:
            self.step()

    def finish_run(self) -> None:
        """Tell the caching functionality that the run is finished and operations such as writing the cache
        file can be performed. Automatically called whenever after a step 'model.running' is false. Can also be manually
        called to force writing the cache without the need of the model reaching the end condition."""
        if self.run_finished:
            print(
                "CacheableModel: tried to finish run that was already finished. Doing nothing."
            )
            return

        # model run finished -> write to cache if in writing state
        if self._cache_state is CacheState.RECORD:
            self._write_cache_file()

        self.run_finished = True

    def step(self) -> None:
        """A single step."""
        self.step_count = self.step_count + 1

        if self._cache_state is CacheState.RECORD:
            self.model.step()
            # Cache only every n-th step
            if self.step_count % self._cache_step_rate == 0:
                self._step_write_to_cache()

        elif self._cache_state is CacheState.REPLAY:
            self._step_read_from_cache()

            # after reading the last step: stop simulation
            if self.step_count == len(self.cache) - 1:
                self.model.running = False

        # if through simulation or replay the model stopped running, let caching know about it
        if not self.model.running:
            self.finish_run()

    def _step_write_to_cache(self) -> None:
        """Is performed for every step, when 'cache_state' is 'RECORD'. Serializes the current state of the model and
        adds it to the cache (which is a list that contains the state for each performed step)."""
        self.cache.append(self._serialize_state())

    def _step_read_from_cache(self) -> None:
        """Is performed for every step, when 'cache_state' is 'REPLAY'. Reads the next state from the cache, deserializes
        it and then updates the model state to this new state."""
        serialized_state = self.cache[self.step_count]
        self._deserialize_state(serialized_state)

    def __getattr__(self, item):
        """Act as proxy: forward all attributes (including function calls) from actual model."""
        return self.model.__getattribute__(item)

    def __setattr__(self, key, value):
        if key == "running":
            self.model.__setattr__(key, value)
        else:
            super().__setattr__(key, value)

    def run_model_until_condition_met(
        self, condition_function: Callable[[Model, int], bool]
    ):
        """Run the model until the given condition is fulfilled or the simulation end is reached.
        Can be used to skip the steps of a replay until a given checkpoint is reached or to simulate until a certain
        condition of interest is met."""
        if not self.model.running:
            raise ValueError("Model 'running' attribute needs to be 'True'.")

        while (
            not condition_function(self.model, self.step_count) and self.model.running
        ):
            self.step()

        if not self.model.running:
            print(
                "Reached end of simulation. Model finished running without the condition becoming fulfilled."
            )
