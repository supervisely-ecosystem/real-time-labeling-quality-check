from typing import List, Type, Union

import supervisely as sly

import src.globals as g
from src.cache import get_issued_id, labels_cache

AVG_AREA_THRESHOLD = 0.2


class BaseCase:
    def __init__(
        self, project_meta: sly.ProjectMeta, annotation: sly.Annotation
    ):  # TODO: Switch to sly.AnnotationInfo.
        self.project_meta = project_meta
        self.annotation = annotation
        self._report: Union[str, None] = None

    @property
    def report(self) -> Union[str, None]:
        return self._report

    @report.setter
    def report(self, value: str):
        self._report = value

    def run_result(self) -> bool:
        raise NotImplementedError()

    def run(self):
        if self.run_result():
            sly.logger.info(
                "[SUCCESS] Test for case %s passed.", self.__class__.__name__
            )
        else:
            # TODO: Create an issue using Issues API.
            # Also, get the error message from the instance of the class.
            sly.logger.info(
                "[FAILED ] Test for case %s failed.", self.__class__.__name__
            )

            issue_id = get_issued_id(
                "TEST ISSUE"
            )  # TODO: Get issue name from the project name.
            if self.report is not None:
                g.spawn_api.issues.add_comment(issue_id, self.report)
                # TODO: Add subissue.

    def cache_labels(self):
        for label in self.annotation.labels:
            labels_cache[label.obj_class.name].append(label)

        sly.logger.debug("Labels were cached.")

    def get_labels_by_class(self, obj_class_name: str) -> List[sly.Label]:
        return labels_cache[obj_class_name]


class NoObjectsCase(BaseCase):
    def run_result(self) -> bool:
        if len(self.annotation.labels) > 0:
            return True
        else:
            self.report = (
                f"No objects were found on the image {self.annotation.image_id}."
            )
            return False


class AllObjectsCase(BaseCase):
    # TODO: Implement effective and fast algorithm for this case.
    @sly.timeit
    def run_result(self) -> bool:
        obj_classes_in_meta = [obj_class for obj_class in self.project_meta.obj_classes]
        obj_classes_in_annotation = []
        for label in self.annotation.labels:
            if label.obj_class not in obj_classes_in_annotation:
                obj_classes_in_annotation.append(label.obj_class)
        sly.logger.debug(
            "Number of objects in project meta: %s, in annotation: %s",
            len(obj_classes_in_meta),
            len(obj_classes_in_annotation),
        )
        return len(obj_classes_in_meta) == len(obj_classes_in_annotation)


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

            # Check if the area of current label not differs from average area more than threshold.
            if self._is_diff_more_than_threshold(
                label.area, average_area, AVG_AREA_THRESHOLD
            ):
                result = False
                sly.logger.debug(
                    "Label with area %s for class %s differs from average area more than %s.",
                    label.area,
                    label_class_name,
                    AVG_AREA_THRESHOLD,  # TODO: Get if from the UI widget.
                )

        self.cache_labels()
        return result

    def _get_average_area(self, labels: List[sly.Label]) -> float:
        # TODO: Implement effective algorithm, to avoid iterating over all labels each time.
        # For example, store current average area and update it each time new label is added.
        area_sum = 0
        for label in labels:
            area_sum += label.area
        return area_sum / len(labels)

    def _is_diff_more_than_threshold(
        self, current_area: float, average_area: float, threshold: float
    ) -> bool:
        abs_diff = abs(current_area - average_area)
        rel_diff = abs_diff / average_area
        sly.logger.debug(
            "Difference between current label area and average area: "
            "%s (absolute), %s (relative).",
            abs_diff,
            rel_diff,
        )
        return rel_diff > threshold


class Test:
    def __init__(
        self,
        cases: List[Type[BaseCase]],
        project_meta: sly.ProjectMeta,
        annotation: sly.Annotation,
    ):
        self._cases = cases
        self.project_meta = project_meta
        self.annotation = annotation
        sly.logger.debug("Created test with %s cases.", len(cases))

    @property
    def cases(self) -> List[Type[BaseCase]]:
        return self._cases

    @cases.setter
    def cases(self, value: List[Type[BaseCase]]):
        self._cases = value

    def run(self):
        for case in self.cases:
            current_case = case(
                project_meta=self.project_meta, annotation=self.annotation
            )
            current_case.run()

        sly.logger.info("All test cases were run.")
