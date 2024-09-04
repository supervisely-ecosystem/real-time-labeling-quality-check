from typing import List, Optional, Union

import supervisely as sly
from supervisely.api.annotation_api import AnnotationInfo

import src.globals as g
import src.ui.settings as settings
from src.cache import get_annotation, get_issued_id, labels_cache
from src.issues import get_top_and_left


class BaseCase:
    enabled = True
    threshold = None

    def __init__(
        self,
        project_info: sly.ProjectInfo,
        project_meta: sly.ProjectMeta,
        annotation_info: AnnotationInfo,
    ):
        self.project_info = project_info
        self.project_meta = project_meta
        self.annotation_info = annotation_info

        self._report: Union[str, None] = None
        self._failed_labels: List[sly.Label] = []

        self.annotation = get_annotation(annotation_info, project_meta)

    @property
    def report(self) -> Union[str, None]:
        return self._report

    @report.setter
    def report(self, value: str):
        self._report = value

    @property
    def failed_labels(self) -> List[sly.Label]:
        return self._failed_labels

    def run_result(self) -> bool:
        raise NotImplementedError()

    @classmethod
    def is_enabled(cls) -> bool:
        raise NotImplementedError()

    @classmethod
    def get_threshold(cls) -> Optional[float]:
        raise NotImplementedError()

    @sly.timeit
    def run(self):
        if self.run_result():
            sly.logger.info(
                "[SUCCESS] Test for case %s passed.", self.__class__.__name__
            )
        else:
            sly.logger.info(
                "[FAILED ] Test for case %s failed.", self.__class__.__name__
            )

            self.create_issue()

    @sly.timeit
    def create_issue(self):
        issue_id = get_issued_id(self.project_info.name)
        if self.report is not None:
            g.spawn_api.issues.add_comment(issue_id, self.report)
            sly.logger.debug("Comment was added to issue %s.", issue_id)

            self.create_subissues(issue_id, self.failed_labels)

    @sly.timeit
    def create_subissues(self, issue_id: int, labels: List[sly.Label]):
        for label in labels:
            top, left = get_top_and_left(label)
            g.spawn_api.issues.add_subissue(
                issue_id,
                [self.annotation.image_id],
                [label.sly_id],
                top,
                left,
                annotation_info=self.annotation_info,
                project_meta=self.project_meta,
            )

    def cache_labels(self):
        for label in self.annotation.labels:
            labels_cache[label.obj_class.name].append(label)

        sly.logger.debug("Labels were cached.")

    def get_labels_by_class(self, obj_class_name: str) -> List[sly.Label]:
        return labels_cache[obj_class_name]


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

            labels = self.get_labels_by_class(label_class_name)
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

            if self._is_diff_more_than_threshold(
                label.area, average_area, self.get_threshold()
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
        )

        self.cache_labels()
        return result

    @classmethod
    def is_enabled(cls) -> bool:
        return settings.average_label_area_case_switch.is_on()

    @classmethod
    def get_threshold(cls) -> Optional[float]:
        return settings.average_label_area_case_input.get_value()

    def _get_average_area(self, labels: List[sly.Label]) -> float:
        # TODO: Implement effective algorithm, to avoid iterating over all labels each time.
        # For example, store current average area and update it each time new label is added.
        area_sum = 0
        for label in labels:
            area_sum += label.area
        return area_sum / len(labels)

    def _is_diff_more_than_threshold(
        self, value: float, average_value: float, threshold: float
    ) -> bool:
        abs_diff = abs(value - average_value)
        rel_diff = abs_diff / average_value
        sly.logger.debug(
            "Difference between value and average value: "
            "%s (absolute), %s (relative).",
            abs_diff,
            rel_diff,
        )
        return rel_diff > threshold


class Test:
    def __init__(
        self,
        project_info: sly.ProjectInfo,
        project_meta: sly.ProjectMeta,
        annotation_info: AnnotationInfo,
    ):
        self.project_info = project_info
        self.project_meta = project_meta
        self.annotation_info = annotation_info

    def run(self):
        # Iterate over subclasses of BaseCase and run them.
        for case in BaseCase.__subclasses__():
            if not case.is_enabled():
                sly.logger.debug("Case %s is disabled, skipping...", case.__name__)
                continue
            current_case = case(
                project_info=self.project_info,
                project_meta=self.project_meta,
                annotation_info=self.annotation_info,
            )
            current_case.run()

        sly.logger.info("All test cases were run.")
