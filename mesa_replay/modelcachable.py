"""
A decorator that wraps the model class of mesa and extends it by caching functionality.

Core Objects: CachableModel, StreamingCachableModel
"""

import os
import io
from pathlib import Path
from enum import Enum
from typing import Any, IO

import dill
import gzip

from mesa import Model


class CacheState(Enum):
    WRITE = (1,)
    READ = 2


def _write_cache_file(cache_file_path: Path, cache_data: list[Any]) -> None:
    """Default function for writing the given cache data to the cache file.
    Used by CachableModel if not replaced by a custom write function.
    Uses dill to dump the data into the file.
    Uses gzip for compression."""
    with gzip.open(cache_file_path, "wb") as file:
        dill.dump(cache_data, file)


def _read_cache_file(cache_file_path: Path) -> list[Any]:
    """Default function for reading the cache data from the cache file.
    Used by CachableModel if not replaced by a custom read function.
    Expects that gzip and dill have been used to write the file."""
    with gzip.open(cache_file_path, "rb") as file:
        return dill.load(file)


def _stream_write_next_chunk_size(stream: IO, size: int):
    """The StreamingCachableModel functionality writes each step into the cache file stream as a separate 'chunk'.
    To enable the stream reading functionality to know how big the next data chunk of the stream is, before every chunk
    the chunk size is written into the stream. This function writes the chunk size into the given stream."""
    chunk_length_bytes = size.to_bytes(length=8, byteorder="little", signed=False)
    stream.write(chunk_length_bytes)


def _stream_read_next_chunk_size(stream):
    """The StreamingCachableModel functionality writes each step into the cache file stream as a separate 'chunk'.
    To enable the stream reading functionality to know how big the next data chunk of the stream is, before every chunk
    the chunk size is written into the stream. This function reads the next chunk size from the stream."""
    return int.from_bytes(stream.read(8), byteorder="little", signed=False)


def _strip_off_unneeded_data_from_model_dict(original_model_dict: dict):
    """If not overwritten by custom serialization, CachableModel persists the complete 'model.__dict__' for every step.
    Not everything that the model dict contains needs to be cached. As most model properties are model-specific, the
    decision of what to store and what not to store is up to the person developing the model, which they can do by
    overwriting the 'CachableModel._serialize_state' function. Some generic optimization, however, can be made:
    Many mesa models use the mesa scheduling and/or the mesa datacollector functionality. The scheduler does not need to
    be cached, therefore, we can remove it. The datacollector stores not only data from the current, but also from the
    previous steps. This we can change, by deleting all data from the previous steps. That is exactly what this function
    does. The original dict of the model is taken as input, copied and then unneeded data is removed from the copy. This
    stripped copy is then returned."""
    dict_copy = dill.copy(original_model_dict)
    dict_copy["schedule"] = None
    if "datacollector" in dict_copy:
        data_collector = dict_copy["datacollector"]

        model_vars: dict = data_collector.model_vars
        for key in model_vars.keys():
            values_list: list = model_vars[key]
            latest_value = values_list[len(values_list) - 1]
            model_vars[key] = [latest_value]

        agent_records: dict = data_collector._agent_records
        if not len(agent_records) == 0:
            latest_agent_record_key = len(agent_records) - 1
            latest_agent_record_value = agent_records[latest_agent_record_key]
            data_collector._agent_records = {
                latest_agent_record_key: latest_agent_record_value
            }

    return dict_copy


class CachableModel:
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

        if self._cache_state is CacheState.READ:
            self._read_cache_file()

    def _serialize_state(self) -> Any:
        """Serialize the model state.
        Can be overwritten to write just parts of the state or other custom behavior.
        Needs to remain compatible with '_deserialize_state'.

        Note that for large model states, it might make sense to add compression during the serialization.
        That way the size of the cache in memory can be reduced. Additionally, while, by default, the resulting output
        cache file is compressed too (see '_write_cache_file'), this is not the case, when using other file handling
        behavior, such as writing to a buffered file stream during every step (see 'StreamingCachableModel'). For such
        use-cases, a way to reduce the size of the resulting output cache file is to compress the individual steps. That
        way, for example, reading the cache from the file stream step by step remains possible, without having to
        load the complete cache into memory. This is not possible, when the complete output file is compressed.
        """
        stripped_dict_model = _strip_off_unneeded_data_from_model_dict(
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
        print("Wrote CachableModel cache file to " + str(self.cache_file_path))

    def _read_cache_file(self) -> None:
        """Read the cache from 'cache_file_path' into memory.
        Can be overwritten to, for example, use a different file format or compression or location.
        Needs to remain compatible with '_write_cache_file'
        """
        self.cache = _read_cache_file(self.cache_file_path)

    def run_model(self) -> None:
        """Run the model until the end condition is reached."""
        # self.model.run_model()
        # Right now if someone has a custom run_model function, they need to overwrite this function too

        while self.model.running:
            self.step()

        self.finish_run()

    def finish_run(self) -> None:
        """Tell the caching functionality that the run is finished and operations such as writing the cache
        file can be performed. Automatically called by the 'run_model' function after the run, but needs to be
        manually called, when calling the steps manually."""
        if self.run_finished:
            print(
                "CachableModel: tried to finish run that was already finished. Doing nothing."
            )
            return

        # model run finished -> write to cache if in writing state
        if self._cache_state is CacheState.WRITE:
            self._write_cache_file()

        self.run_finished = True

    def step(self) -> None:
        """A single step."""
        if self._cache_state is CacheState.WRITE:
            self.model.step()
            # Cache only every n-th step
            if (self.step_count + 1) % self._cache_step_rate == 0:
                self._step_write_to_cache()

        elif self._cache_state is CacheState.READ:
            self._step_read_from_cache()

            # after reading the last step: stop simulation
            if self.step_count == len(self.cache) - 1:
                self.model.running = False

        self.step_count = self.step_count + 1

    def _step_write_to_cache(self) -> None:
        """Is performed for every step, when 'cache_state' is 'WRITE'. Serializes the current state of the model and
        adds it to the cache (which is a list that contains the state for each performed step)."""
        self.cache.append(self._serialize_state())

    def _step_read_from_cache(self) -> None:
        """Is performed for every step, when 'cache_state' is 'READ'. Reads the next state from the cache, deserializes
        it and then updates the model state to this new state."""
        serialized_state = self.cache[self.step_count]
        self._deserialize_state(serialized_state)

    def __getattr__(self, item):
        """Act as proxy: forward all attributes (including function calls) from actual model."""
        return self.model.__getattribute__(item)


class StreamingCachableModel(CachableModel):
    """Decorator for CachableModelOptimized that uses buffered streams for reading and writing the cache, instead
    of keeping the complete cache in memory. Useful when the cache is large."""

    def __init__(
        self,
        model: Model,
        cache_file_path: str | Path,
        cache_state: CacheState,
        cache_step_rate: int = 1,
    ):
        super().__init__(model, cache_file_path, cache_state, cache_step_rate)

        if cache_state is CacheState.WRITE:
            if self.cache_file_path.exists():
                print(
                    "CachableModelLarge: cache file (path='"
                    + str(self.cache_file_path)
                    + "') already exists. "
                    "Deleting it."
                )
                os.remove(cache_file_path)
            self.cache_file_stream = io.open(cache_file_path, "wb")

        elif cache_state is CacheState.READ:
            self.cache_file_stream = io.open(cache_file_path, "rb")

    def finish_run(self) -> None:
        """Tell the caching functionality that the run is finished and operations such as writing the cache
        file can be performed. Automatically called by the 'run_model' function after the run, but needs to be
        manually called, when calling the steps manually."""
        super().finish_run()
        self.cache_file_stream.close()

    def _step_write_to_cache(self) -> None:
        """Is performed for every step, when 'cache_state' is 'WRITE'. Serializes the current state of the model and
        writes it to the cache file stream."""
        serialized_state: bytes = self._serialize_state()
        _stream_write_next_chunk_size(self.cache_file_stream, len(serialized_state))
        self.cache_file_stream.write(serialized_state)

    def _step_read_from_cache(self) -> None:
        """Is performed for every step, when 'cache_state' is 'READ'. Reads the next state from the cache file stream,
        deserializes it and then updates the model state to this new state."""
        chunk_length = _stream_read_next_chunk_size(self.cache_file_stream)
        if chunk_length == 0:
            print("CachableModelLarge: reached end of cache file stream.")
            self.model.running = False
        else:
            serialized_state = self.cache_file_stream.read(chunk_length)
            self._deserialize_state(serialized_state)

    def _write_cache_file(self) -> None:
        """Overwrites the '_write_cache_file' function of the CachableModel class. As the file content is written
        to the stream during each step, this function does not have to write the complete cache file.
        It only adds an EOF hint to the cache file stream. After that, the stream can be closed and the cache file is
        completed.
        """
        # end cache file with a chunk size of 0, to make EOF detectable
        _stream_write_next_chunk_size(self.cache_file_stream, 0)

    def _read_cache_file(self) -> None:
        """Overwrites the '_read_cache_file' function of the CachableModel class. As the file content is read from
        the stream during each step, this function does not have to do anything in advance."""
        return
