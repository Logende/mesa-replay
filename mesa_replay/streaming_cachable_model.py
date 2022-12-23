"""
A decorator that makes CachableModel use IO buffered streaming to write to the cache file/read from the cache file step
by step, instead of keeping the complete cache in memory.

Core Objects: StreamingCachableModel
"""

import os
import io
from pathlib import Path
from typing import IO

from mesa_replay.cachable_model import Model, CachableModel, CacheState


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


class StreamingCachableModel(CachableModel):
    """Decorator for CachableModel that uses buffered streams for reading and writing the cache, instead
    of keeping the complete cache in memory. Useful when the cache is large."""

    def __init__(
        self,
        model: Model,
        cache_file_path: str | Path,
        cache_state: CacheState,
        cache_step_rate: int = 1,
    ):

        if cache_state is CacheState.WRITE:
            if cache_file_path.exists():
                print(
                    "CachableModelLarge: cache file (path='"
                    + str(cache_file_path)
                    + "') already exists. "
                    "Deleting it."
                )
                os.remove(cache_file_path)
            self.cache_file_stream = io.open(cache_file_path, "wb")

        elif cache_state is CacheState.READ:
            self.cache_file_stream = io.open(cache_file_path, "rb")

        # needs to be called when the file stream is already open
        super().__init__(model, cache_file_path, cache_state, cache_step_rate)

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
