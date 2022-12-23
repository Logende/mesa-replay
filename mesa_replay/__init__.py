"""
Mesa-Replay
Core Objects: CachableModel, CachableModelStreaming
"""
import datetime

from mesa_replay.cachable_model import CachableModel, CacheState
from mesa_replay.streaming_cachable_model import StreamingCachableModel

__all__ = ["CachableModel", "StreamingCachableModel", "CacheState"]

__title__ = "mesa-replay"
__version__ = "0.1.0"
__license__ = "Apache 2.0"
__copyright__ = "Copyright %s Project Mesa-Replay Team" % datetime.date.today().year
