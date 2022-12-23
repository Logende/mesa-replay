"""
Mesa-Replay
Core Objects: CachableModel, CachableModelStreaming
"""
import datetime

from mesa_replay.modelcachable import ModelCachable, ModelCachableStreaming

__all__ = [
    "ModelCachable",
    "ModelCachableStreaming"
]

__title__ = "Mesa-Replay"
__version__ = "0.1.0"
__license__ = "Apache 2.0"
__copyright__ = f"Copyright {datetime.date.today().year} Felix Neubauer"
__copyright__ = "Copyright %s Project Mesa-Replay Team" % datetime.date.today().year
