from typing import List, Optional

import supervisely as sly

import src.globals as g
from src.cache import Cache
from src.test import BaseCase
from src.utils import group_labels_by_class, is_diff_more_than_threshold


class NoObjectsCase(BaseCase):
    """This case checks if there are any objects (labels) in the annotation."""

    @sly.timeit
    def run_result(self) -> bool:
        """Checks if there are any objects in the annotation.

        :return: True if there are objects, False otherwise.
        :rtype: bool
        """
        if len(self.annotation.labels) > 0:
            return True
        else:
            self.report = "No objects were found on the image."
            return False

    @classmethod
    def is_enabled(cls) -> bool:
        """Checks if the case is enabled in the (switch widget in the UI) settings.

        :return: True if the case is enabled, False otherwise.
        :rtype: bool
        """
        return g.no_objects_case_enabled


class AllObjectsCase(BaseCase):
    """This case checks if all objects from the project meta are present on the image."""

    @sly.timeit
    def run_result(self) -> bool:
        """Checks if all objects from the project meta are present on the image.

        :return: True if all objects are present, False otherwise.
        :rtype: bool
        """
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
            missing_classes = obj_classes_in_meta - obj_classes_in_annotation
            missing_class_names = [obj_class.name for obj_class in missing_classes]

            self.report = f"The following classes are missing on the image: {missing_class_names}."
            return False

    @classmethod
    def is_enabled(cls) -> bool:
        """Checks if the case is enabled in the (switch widget in the UI) settings.

        :return: True if the case is enabled, False otherwise.
        :rtype: bool
        """
        return g.all_objects_case_enabled


class AverageLabelAreaCase(BaseCase):
    """This case checks if the area of each label is close to the average area of the class."""

    @sly.timeit
    def run_result(self) -> bool:
        """Checks if the area of each label is close to the average area of the class.

        :return: True if the areas are close, False otherwise.
        :rtype: bool
        """
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

        if not result:
            self.report = (
                "The labels with following IDs have area that differs from average area "
                f"more than specified threshold of {self.get_threshold()}: "
                f"{[label.sly_id for label in self.failed_labels]}."
            )

        return result

    @classmethod
    def is_enabled(cls) -> bool:
        """Checks if the case is enabled in the (switch widget in the UI) settings.

        :return: True if the case is enabled, False otherwise.
        :rtype: bool
        """
        return g.average_label_area_case_enabled

    @classmethod
    def get_threshold(cls) -> Optional[float]:
        """Gets the threshold value from the (input widget in the UI) settings.

        :return: The threshold value.
        :rtype: float
        """
        return g.average_label_area_case_theshold

    def _get_average_area(self, labels: List[sly.Label]) -> float:
        """Calculates the average area of the labels.

        :param labels: The list of labels.
        :type labels: List[sly.Label]
        :return: The average area of the labels.
        :rtype: float
        """
        area_sum = 0
        for label in labels:
            area_sum += label.area
        return area_sum / len(labels)


class AverageNumberOfClasLabelsCase(BaseCase):
    """This case checks if the number of labels for each class is close to the average number of
    labels for the class."""

    @sly.timeit
    def run_result(self) -> bool:
        """Checks if the number of labels for each class is close to the average number of labels
        for the class.

        :return: True if the numbers are close, False otherwise.
        :rtype: bool
        """
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
            if number_of_images_with_class < 1:
                sly.logger.debug(
                    "Not enough images with class %s to calculate average number of labels.",
                    class_name,
                )
                continue

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

        if not result:
            self.report = (
                "The number of labels for classes "
                f"{failed_class_names} differs from average more than specified threshold of: "
                f"{self.get_threshold()}."
            )

        return result

    @classmethod
    def is_enabled(cls) -> bool:
        """Checks if the case is enabled in the (switch widget in the UI) settings.

        :return: True if the case is enabled, False otherwise.
        :rtype: bool
        """
        return g.average_number_of_class_labels_case_enabled

    @classmethod
    def get_threshold(cls) -> Optional[float]:
        """Gets the threshold value from the (input widget in the UI) settings.

        :return: The threshold value.
        :rtype: float
        """
        return g.average_number_of_class_labels_case_theshold
