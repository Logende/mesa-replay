"""
Mesa-Replay
Core Objects: CacheableModel, CacheableModelStreaming, CacheState
"""
import datetime

from mesa_replay.cacheable_model import CacheableModel, CacheState
from mesa_replay.streaming_cacheable_model import StreamingCacheableModel

__all__ = ["CacheableModel", "StreamingCacheableModel", "CacheState"]

__title__ = "mesa-replay"
__version__ = "0.1.0"
__license__ = "Apache 2.0"
__copyright__ = "Copyright %s Project Mesa-Replay Team" % datetime.date.today().year
