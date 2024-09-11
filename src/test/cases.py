from collections import defaultdict
from typing import Dict, List, Optional

import supervisely as sly

import src.ui.settings as settings
from src.cache import Cache
from src.test import BaseCase


class NoObjectsCase(BaseCase):
    @sly.timeit
    def run_result(self) -> bool:
        if len(self.annotation.labels) > 0:
            return True
        else:
            self.report = (
                "No objects were found on the image with ID: "
                f"{self.annotation_info.image_id}."
            )
            return False

    @classmethod
    def is_enabled(cls) -> bool:
        return settings.no_objects_case_switch.is_on()


class AllObjectsCase(BaseCase):
    @sly.timeit
    def run_result(self) -> bool:
        obj_classes_in_meta = {obj_class for obj_class in self.project_meta.obj_classes}
        obj_classes_in_annotation = {
            label.obj_class for label in self.annotation.labels
        }

        sly.logger.debug(
            "Number of objects in project meta: %s, in annotation: %s",
            len(obj_classes_in_meta),
            len(obj_classes_in_annotation),
        )
        if obj_classes_in_meta == obj_classes_in_annotation:
            return True
        else:
            self.report = (
                "Not all objects from project meta were found on the image with ID: "
                f"{self.annotation_info.image_id}."
            )
            return False

    @classmethod
    def is_enabled(cls) -> bool:
        return settings.all_objects_case_switch.is_on()


class AverageLabelAreaCase(BaseCase):
    @sly.timeit
    def run_result(self) -> bool:
        result = True
        for label in self.annotation.labels:
            label_class_name = label.obj_class.name

            labels = Cache().get_labels_by_class(self.project_info.id, label_class_name)
            if len(labels) < 1:
                sly.logger.debug(
                    "Not enough labels for class %s to calculate average area.",
                    label_class_name,
                )
                continue

            average_area = self._get_average_area(labels)
            sly.logger.debug(
                "Average area for class %s is %s.", label_class_name, average_area
            )

            if is_diff_more_than_threshold(
                label.area, average_area, self.get_threshold()  # type: ignore
            ):
                result = False
                sly.logger.debug(
                    "Label with area %s for class %s differs from average area more than %s.",
                    label.area,
                    label_class_name,
                    self.get_threshold(),
                )

                if label not in self.failed_labels:
                    self.failed_labels.append(label)

        self.report = (
            "The labels with following IDs have area that differs from average area "
            f"more than {self.get_threshold()}: {[label.sly_id for label in self.failed_labels]}."
            f"On the image with ID: {self.annotation_info.image_id}."
        )

        return result

    @classmethod
    def is_enabled(cls) -> bool:
        return settings.average_label_area_case_switch.is_on()

    @classmethod
    def get_threshold(cls) -> Optional[float]:
        return settings.average_label_area_case_input.get_value()

    def _get_average_area(self, labels: List[sly.Label]) -> float:
        area_sum = 0
        for label in labels:
            area_sum += label.area
        return area_sum / len(labels)


class AverageNumberOfClasLabelsCase(BaseCase):
    @sly.timeit
    def run_result(self) -> bool:
        # 1. Group labels in annotation by class to know for each class how many
        # labels are on the image.
        # 2. Group labels of the class from cache by images to know what is
        # the average number of labels for the class on one image.
        # 3. Iterate over class label groups and compare the number of labels
        # on the current image with the average number of labels for the class.

        class_labels_in_annotation = group_labels_by_class([self.annotation])
        class_annotations_in_cache = Cache().group_annotations_by_class(
            self.project_info.id
        )
        result = True
        failed_class_names = []

        for class_name, labels in class_labels_in_annotation.items():
            number_of_labels = len(labels)
            sly.logger.debug(
                "Number of labels for class %s is %s.", class_name, number_of_labels
            )
            class_annotations = class_annotations_in_cache.get(class_name, [])
            number_of_images_with_class = len(class_annotations)

            class_labels_in_cache = group_labels_by_class(class_annotations).get(
                class_name, []
            )

            average_number_of_labels = (
                len(class_labels_in_cache) / number_of_images_with_class
            )
            sly.logger.debug(
                "Average number of labels for class %s is %s.",
                class_name,
                average_number_of_labels,
            )

            if is_diff_more_than_threshold(
                number_of_labels, average_number_of_labels, self.get_threshold()  # type: ignore
            ):
                result = False
                sly.logger.debug(
                    "Number of labels for class %s differs from average more than %s.",
                    class_name,
                    self.get_threshold(),
                )

                failed_class_names.append(class_name)

            # TODO: Updated cached information about average number of labels for class.

        self.report = (
            "The number of labels for classes "
            f"{failed_class_names} differs from average more than {self.get_threshold()}."
            f"On the image with ID: {self.annotation_info.image_id}."
        )

        return result

    @classmethod
    def is_enabled(cls) -> bool:
        return settings.average_number_of_class_labels_case_switch.is_on()

    @classmethod
    def get_threshold(cls) -> Optional[float]:
        return settings.average_number_of_class_labels_case_input.get_value()


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
