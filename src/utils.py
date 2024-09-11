from collections import defaultdict
from typing import Dict, List

import supervisely as sly


def dummy(*args, **kwargs):
    """Dummy function to be used to register a callback for widgets.
    It does nothing.
    """
    pass


def is_diff_more_than_threshold(
    value: float, average_value: float, threshold: float
) -> bool:
    abs_diff = abs(value - average_value)
    rel_diff = abs_diff / average_value
    sly.logger.debug(
        "Difference between value and average value: " "%s (absolute), %s (relative).",
        abs_diff,
        rel_diff,
    )
    return rel_diff > threshold


def group_labels_by_class(
    annotations: List[sly.Annotation],
) -> Dict[str, List[sly.Label]]:
    result = defaultdict(list)

    for annotation in annotations:
        for label in annotation.labels:
            result[label.obj_class.name].append(label)

    return result
