from mesa_replay.cachablemodel import Model, CacheState

from mesa_replay.streamingcachablemodel import (
    StreamingCachableModel,
    _stream_read_next_chunk_size,
)

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path


class ModelFibonacci(Model):
    """Simple fibonacci model to be used by the tests."""

    previous = 0
    current = 1

    def step(self):
        new_value = self.previous + self.current
        self.previous = self.current
        self.current = new_value
        if new_value > 100000:
            self.running = False

    def custom_model_function(self):
        return self.current


class ModelFibonacciForReplay(ModelFibonacci):
    """Same as the fibonacci model, except it does not support simulating a step and instead will raise an Exception
    if simulating a step is attempted. To be used by tests to verify that replay from cache does not simply simulate
    again, but instead actually reads from the cache."""

    def step(self):
        raise Exception("This function is not supposed to be called during replay.")


class TestCachableModel(unittest.TestCase):
    def test_streaming_chunk_handling(self):
        """This test verifies that the streaming functionality of 'StreamingCachableModel' works properly:
        for every step, first the size of the chunk (state) to persist is written to the stream. Next the actual
        chunk is written."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path = Path(tmp_dir_path).joinpath("cache_file")

            # Simulate
            model_simulate = ModelFibonacci()
            model_simulate = StreamingCachableModel(
                model_simulate, cache_file_path, CacheState.WRITE
            )
            model_simulate.step()
            model_simulate.finish_run()
            value_simulate = model_simulate.current

            # Replay
            model_replay = ModelFibonacciForReplay()
            model_replay = StreamingCachableModel(
                model_replay, cache_file_path, CacheState.READ
            )

            # manually read from stream: 1. retrieve chunk length
            chunk_length = _stream_read_next_chunk_size(model_replay.cache_file_stream)
            assert chunk_length > 0

            # 2. read the actual state data by using the given chunk length
            serialized_state = model_replay.cache_file_stream.read(chunk_length)

            # 3. set model state to deserialized chunk state
            model_replay._deserialize_state(serialized_state)

            # expect that the simulation of 1 step has the same value as replay of 1 chunk
            value_replay = model_replay.current
            assert value_replay == value_simulate

    def test_streaming_results(self):
        """This test uses StreamingCachableModel. It runs a complete simulation, that is persisted using streaming.
        Next it replays the simulation using the cache and streaming. Finally, it asserts that the final value of the
        replay is the same as the final value of the simulation."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path = Path(tmp_dir_path).joinpath("cache_file")

            # Simulate
            model_simulate = ModelFibonacci()
            model_simulate = StreamingCachableModel(
                model_simulate, cache_file_path, CacheState.WRITE
            )
            model_simulate.run_model()
            value_simulate = model_simulate.current

            # Replay
            model_replay = ModelFibonacciForReplay()
            model_replay = StreamingCachableModel(
                model_replay, cache_file_path, CacheState.READ
            )
            model_replay.run_model()
            value_replay = model_replay.current

            assert value_replay == value_simulate
