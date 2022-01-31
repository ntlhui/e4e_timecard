from __future__ import annotations

from abc import ABC, abstractclassmethod, abstractmethod
from typing import Any, Dict, Type, TypeVar, Optional
from uuid import UUID

T = TypeVar('T')
class Serializable (ABC):
    @abstractmethod
    def toDict(self) -> Dict[str, Any]:
        pass

    @abstractclassmethod
    def fromDict(cls, data: Dict[str, Any]):
        pass

    @abstractmethod
    def isComplete(self) -> bool:
        pass

    @abstractmethod
    def complete(self, objects: Dict[UUID, Serializable]):
        pass

    def _resolveObj(self, id: UUID, t: Type[T], objects: Dict[UUID, Serializable]) -> Optional[T]:
        if id in objects:
            obj = objects[id]
            if isinstance(obj, t):
                return obj
            else:
                raise RuntimeError(f'Expected {id} to be {t}, got {type(obj)} instead!')
        return None
