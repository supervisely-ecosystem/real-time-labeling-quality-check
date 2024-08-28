from typing import List, Type

import supervisely as sly


class BaseCase:
    def __init__(self, project_meta: sly.ProjectMeta, annotation: sly.Annotation):
        self.project_meta = project_meta
        self.annotation = annotation

    def run_result(self) -> bool:
        raise NotImplementedError()

    def run(self):
        if self.run_result():
            sly.logger.info(
                "[SUCCESS] Test for case %s passed.", self.__class__.__name__
            )
        else:
            # TODO: Create an issue using Issues API.
            sly.logger.info(
                "[FAILED ] Test for case %s failed.", self.__class__.__name__
            )


class NoObjectsCase(BaseCase):
    def run_result(self) -> bool:
        return len(self.annotation.labels) > 0


class AllObjectsCase(BaseCase):
    # TODO: Implement effective and fast algorithm for this case.
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
