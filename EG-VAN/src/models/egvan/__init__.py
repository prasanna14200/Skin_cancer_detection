"""Documented EG-VAN architecture reconstruction; separate from frozen baseline."""

from .egvan import EGVAN, build_nine_class_egvan

__all__ = ["EGVAN", "build_nine_class_egvan"]
