from typing import List, Type

import supervisely as sly


class BaseCase:
    def __init__(self, project_id: int, annotation: sly.Annotation):
        self.project_id = project_id
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


class Test:
    def __init__(
        self, cases: List[Type[BaseCase]], project_id: int, annotation: sly.Annotation
    ):
        self._cases = cases
        self.project_id = project_id
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
            current_case = case(project_id=self.project_id, annotation=self.annotation)
            current_case.run()

        sly.logger.info("All test cases were run.")
