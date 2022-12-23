"""
Mesa-Replay
Core Objects: CachableModel, CachableModelStreaming
"""
import datetime

from mesa_replay.modelcachable import CachableModel, StreamingCachableModel, CacheState

__all__ = ["CachableModel", "StreamingCachableModel", "CacheState"]

__title__ = "Mesa-Replay"
__version__ = "0.1.0"
__license__ = "Apache 2.0"
__copyright__ = "Copyright %s Project Mesa-Replay Team" % datetime.date.today().year
