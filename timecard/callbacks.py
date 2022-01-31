from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Tuple


@dataclass
class Callback:
    fn: Callable
    kwargs: Dict[str, Any] = field(default_factory=dict)
    args: Tuple = field(default_factory=tuple)
