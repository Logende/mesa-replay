import gzip
import lzma
import dill

from mesa_replay.cacheable_model import Model, CacheableModel, CacheState

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


class CacheableModelCustomFileHandling(CacheableModel):
    """CacheableModel with custom write and read implementation for the cache file. Uses a different compression
    algorithm than the default CacheableModel, which should perform slower but result in stronger compression.
    Used in a test to demonstrate the possibility of writing custom file handling."""

    def _write_cache_file(self) -> None:
        # overwrite to use different compression algorithm
        with lzma.open(self.cache_file_path, "wb") as file:
            dill.dump(self.cache, file)

    def _read_cache_file(self) -> None:
        # overwrite to use different compression algorithm
        with lzma.open(self.cache_file_path, "rb") as file:
            self.cache = dill.load(file)


class CacheableModelCustomSerialization(CacheableModel):
    """CacheableModel with custom state serialization and deserialization implementation for the cache.
    Instead of storing the complete model instance state, it stores just the values necessary for replay.
    In case of ModelFibonacci, storing the 'current' value is enough for replay."""

    def _serialize_state(self) -> int:
        # Store just the current value, because this is sufficient for replay. Note that for other models,
        # one could also store a list of selected attributes or anything else that is sufficient for replay.
        return self.model.current

    def _deserialize_state(self, state: int) -> None:
        # As the serialization (see function above) stores just the current value, the state that the deserialization
        # function receives is exactly this one value. So, to deserialize, it suffices to transfer that state (current
        # model value) to the model instance that is used for replay.
        self.model.current = state


class TestCacheableModel(unittest.TestCase):
    def test_model_attribute_access_over_wrapper(self):
        """The actual simulation model is wrapped inside a CacheableModel instance.
        The new model variable (which is of type CacheableModel and no longer of type ModelFibonacci) should
        still behave the same way as the actual simulation model from outside. It should be possible to access the
        attributes and functions of the underlying simulation model without knowing about the use of CacheableModel.
        CacheableModel follows the decorator pattern: it adds functionality to the model, but from an outside perspective
        the object can be still accessed the same way as before."""
        model = ModelFibonacci()
        model = CacheableModel(model, "irrelevant_cache_file_path", CacheState.RECORD)
        assert model.running is True
        assert model.previous == 0
        assert model.custom_model_function() == 1

    def test_cache_read_fail_when_non_existing_file(self):
        """When we instantiate a CacheableModel with 'CacheState.REPLAY' it (within its constructor) tries to load
        the cache from the given cache path. If the cache file does not exist or is not of the expected format, an
        exception is thrown."""
        model = ModelFibonacci()

        # No exception when constructing CacheableModel with CacheState.RECORD because does not try to read cache
        CacheableModel(model, "non_existing_file", CacheState.RECORD)

        # Exception when trying to construct CacheableModel with CacheState.REPLAY and non-existing cache file
        self.assertRaises(
            Exception, CacheableModel, model, "non_existing_file", CacheState.REPLAY
        )

        # Exception when trying to construct CacheableModel with CacheState.REPLAY and invalid cache file
        with TemporaryDirectory() as tmp_dir_path:
            broken_cache_file_path = Path(tmp_dir_path).joinpath("broken_cache_file")
            with open(broken_cache_file_path, "w") as broken_cache_file:
                broken_cache_file.write("invalid content")
            self.assertRaises(
                Exception, CacheableModel, model, broken_cache_file_path, CacheState.REPLAY
            )

    def test_cache_file_creation(self):
        """When a model is simulated and CacheableModel with 'CacheState.RECORD' is used, the simulation steps are
        written to a cache. At the end of the simulation process (when 'CacheableModel.finish_run()' is called) the
         cache is persisted by writing to the given 'cache_file_path'."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path = Path(tmp_dir_path).joinpath("cache_file")

            # Before simulation: cache file does not yet exist
            assert not cache_file_path.is_file() and not cache_file_path.exists()

            # Simulate
            model_simulate = ModelFibonacci()
            model_simulate = CacheableModel(
                model_simulate, cache_file_path, CacheState.RECORD
            )
            for i in range(10):
                model_simulate.step()
            model_simulate.finish_run()

            # After finished run: cache file does exist
            assert cache_file_path.is_file()

            # assert that file created by default CacheableModel can be opened using gzip and then dill
            with gzip.open(cache_file_path, "rb") as file:
                dill.load(file)

    def test_compare_replay_with_simulation(self):
        """When replaying a simulation using the caching functionality, the replay should result in the model having
        the same attributes in every step, as it had during the simulation."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path = Path(tmp_dir_path).joinpath("cache_file")
            step_count = 20
            values_simulate = []
            values_replay = []

            # Simulate
            model_simulate = ModelFibonacci()
            model_simulate = CacheableModel(
                model_simulate, cache_file_path, CacheState.RECORD
            )
            for i in range(step_count):
                model_simulate.step()
                values_simulate.append(model_simulate.current)
            model_simulate.finish_run()

            # Replay
            model_replay = ModelFibonacciForReplay()
            model_replay = CacheableModel(model_replay, cache_file_path, CacheState.REPLAY)
            for i in range(step_count):
                model_replay.step()
                values_replay.append(model_replay.current)

            # Assert that values are identical
            assert values_replay == values_simulate

    def test_cache_size(self):
        """When caching a simulation for n steps and then replaying it, the replay should end at the exact same step as
        the simulation did."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path = Path(tmp_dir_path).joinpath("cache_file")
            step_count = 20

            # Simulate
            model_simulate = ModelFibonacci()
            model_simulate = CacheableModel(
                model_simulate, cache_file_path, CacheState.RECORD
            )
            for i in range(step_count):
                model_simulate.step()
            model_simulate.finish_run()

            # Load from cache
            model_replay = ModelFibonacciForReplay()
            model_replay = CacheableModel(model_replay, cache_file_path, CacheState.REPLAY)

            # expect that cache is 1 bigger than step count because it includes the initial state (before any step) too
            assert len(model_replay.cache) == step_count + 1

    def test_automatic_detection_of_run_finish(self):
        """When using the 'CacheableModel.run_model()' function, the simulation will simulate steps until it reaches
        'model.running=False'. When it reaches this end condition and stops running, the 'CacheableModel.finish_run()'
        function should automatically be called to persist the cache."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path = Path(tmp_dir_path).joinpath("cache_file")

            model_simulate = ModelFibonacci()
            model_simulate = CacheableModel(
                model_simulate, cache_file_path, CacheState.RECORD
            )

            assert not model_simulate.run_finished

            model_simulate.run_model()

            assert model_simulate.run_finished

    def test_replay_finish_identical_to_simulation_finish(self):
        """This test lets the simulation run until it reaches 'running=False'. Then the cache is automatically
        persisted. Next the simulation is replayed by reading from the cache. We assert that the replay stops at the
        same step as the simulation and that it stops with the same result state/value too. This test differs only
        slightly from 'test_cache_size' by using the 'run_model' function instead of simulating a pre-defined step count.
        """
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path = Path(tmp_dir_path).joinpath("cache_file")

            # Simulate
            model_simulate = ModelFibonacci()
            model_simulate = CacheableModel(
                model_simulate, cache_file_path, CacheState.RECORD
            )
            model_simulate.run_model()
            final_value_simulation = model_simulate.current
            final_step_simulation = model_simulate.step_count

            # Replay
            model_replay = ModelFibonacciForReplay()
            model_replay = CacheableModel(model_replay, cache_file_path, CacheState.REPLAY)
            model_replay.run_model()
            final_value_replay = model_simulate.current
            final_step_replay = model_replay.step_count

            assert final_step_replay == final_step_simulation
            assert final_value_replay == final_value_simulation

    def test_cache_step_rate(self):
        """This test verifies that when using 'cache_step_rate' > 1 the cache will store
        correspondingly fewer steps. The idea of cache_step_rate is that it enables storing only every n-th step, making
        it possible to drastically reduce cache size and increase replay performance."""
        for cache_step_rate in (1, 2, 3, 8):
            with TemporaryDirectory() as tmp_dir_path:
                cache_file_path = Path(tmp_dir_path).joinpath("cache_file")
                step_count = 20

                # Simulate
                model_simulate = ModelFibonacci()
                model_simulate = CacheableModel(
                    model_simulate,
                    cache_file_path,
                    CacheState.RECORD,
                    cache_step_rate=cache_step_rate,
                )
                for i in range(step_count):
                    model_simulate.step()
                model_simulate.finish_run()

                # Replay
                model_replay = ModelFibonacciForReplay()
                model_replay = CacheableModel(
                    model_replay, cache_file_path, CacheState.REPLAY
                )

                # The replay cache stores only every n-th step. E.g. cache_step_rate is 2: only every second step.
                # 100 steps, cache_step_rate 1 -> 100 steps cached
                # 100 steps, cache_step_rate 2 -> 50 steps cached
                # 100 steps, cache_step_rate 3 -> 33 steps cached
                # 100 steps, cache_step_rate 8 -> 12 steps cached
                expected_replay_steps = step_count // cache_step_rate

                assert len(model_replay.cache) == expected_replay_steps + 1

                model_replay.run_model()
                assert model_replay.step_count == expected_replay_steps

    def test_custom_cache_file_handling(self):
        """This test compares the cache file outputs from CacheableModel versus CacheableModelCustomFileHandling.
        The latter implements custom file handling and uses a stronger compression. The resulting cache file should be
        smaller than the one from the default CacheableModel.
        This test mainly serves as demonstration on how custom file handling could be implemented."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path_1 = Path(tmp_dir_path).joinpath("cache_file_1")
            cache_file_path_2 = Path(tmp_dir_path).joinpath("cache_file_2")

            # Simulate with regular CacheableModel
            model_1 = ModelFibonacci()
            model_1 = CacheableModel(model_1, cache_file_path_1, CacheState.RECORD)
            model_1.run_model()
            final_value_1 = model_1.current

            # Simulate with custom CacheableModel that uses stronger compression
            model_2 = ModelFibonacci()
            model_2 = CacheableModelCustomFileHandling(
                model_2, cache_file_path_2, CacheState.RECORD
            )
            model_2.run_model()
            final_value_2 = model_2.current

            # Make sure both models behaved the same way
            assert final_value_1 == final_value_2

            # Cache file 2 should be smaller than cache file 1 due to stronger compression
            assert (
                cache_file_path_2.stat().st_size * 1.1
                < cache_file_path_1.stat().st_size
            )

    def test_custom_serialization(self):
        """This test compares the cache file outputs from CacheableModel versus CacheableModelCustomSerialization.
        The latter implements custom state serialization and deserialization. Instead of storing the complete model
        state, it stores only the 'current' value of the model in the cache. The resulting cache file should be
        significantly smaller than the one from the default CacheableModel.
        This test mainly serves as demonstration on how custom state serialization can be implemented."""
        with TemporaryDirectory() as tmp_dir_path:
            cache_file_path_1 = Path(tmp_dir_path).joinpath("cache_file_1")
            cache_file_path_2 = Path(tmp_dir_path).joinpath("cache_file_2")

            # Simulate with regular CacheableModel
            model_1 = ModelFibonacci()
            model_1 = CacheableModel(model_1, cache_file_path_1, CacheState.RECORD)
            model_1.run_model()
            final_value_1 = model_1.current

            # Simulate with custom CacheableModel that caches only parts of the model state that are required for replay
            model_2 = ModelFibonacci()
            model_2 = CacheableModelCustomSerialization(
                model_2, cache_file_path_2, CacheState.RECORD
            )
            model_2.run_model()
            final_value_2 = model_2.current

            # Make sure both models behaved the same way
            assert final_value_1 == final_value_2

            # Cache file 2 should be a lot smaller than cache file 1 due to storing fewer data
            assert (
                cache_file_path_2.stat().st_size * 35 < cache_file_path_1.stat().st_size
            )
