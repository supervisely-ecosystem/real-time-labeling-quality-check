from typing import List, Optional, Union

import supervisely as sly
from supervisely.api.annotation_api import AnnotationInfo
from supervisely.imaging.image import get_new_labeling_tool_url

import src.globals as g
import src.ui.settings as settings
from src.cache import Cache
from src.issues import get_top_and_left


class BaseCase:
    enabled = True
    threshold = None

    def __init__(
        self,
        project_info: sly.ProjectInfo,
        project_meta: sly.ProjectMeta,
        annotation_info: AnnotationInfo,
        **kwargs,
    ):
        self.project_info = project_info
        self.project_meta = project_meta
        self.annotation_info = annotation_info

        self._report: Union[str, None] = None
        self._failed_labels: List[sly.Label] = []

        self.annotation = Cache().get_annotation(
            annotation_info, project_meta, project_info
        )

        self.kwargs = kwargs

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
    def run(self) -> Optional[str]:
        if self.run_result():
            sly.logger.info(
                "[SUCCESS] Test for case %s passed.", self.__class__.__name__
            )
        else:
            sly.logger.info(
                "[FAILED ] Test for case %s failed.", self.__class__.__name__
            )

            self.create_issue()

        return self.report

    @sly.timeit
    def create_issue(self):
        issue_id = Cache().get_issued_id(self.project_info.name)

        # Create issue only if the switch is on and if the report is not empty.
        if self.report is not None and settings.create_issues_switch.is_on():
            # Add a link to the image to the report.
            report_with_link = self.add_link_to_report(self.report)

            g.spawn_api.issues.add_comment(issue_id, report_with_link)
            sly.logger.debug("Comment was added to issue %s.", issue_id)

            self.create_subissues(issue_id, self.failed_labels)

    @sly.timeit
    def create_subissues(self, issue_id: int, labels: List[sly.Label]):
        for label in labels:
            top, left = get_top_and_left(label)
            g.spawn_api.issues.add_subissue(
                issue_id,
                [self.annotation.image_id],
                [label.sly_id],  # type: ignore
                top,
                left,
                annotation_info=self.annotation_info,
                project_meta=self.project_meta,
            )

    def add_link_to_report(self, report: str) -> str:
        try:
            url = get_new_labeling_tool_url(**self.kwargs)
        except Exception as e:
            sly.logger.warn("Failed to get the link to the image: %s", e)
            return report

        return f"{report}\n\n [Link to the image]({url})"


class Test:
    def __init__(
        self,
        project_info: sly.ProjectInfo,
        project_meta: sly.ProjectMeta,
        annotation_info: AnnotationInfo,
        **kwargs,
    ):
        self.project_info = project_info
        self.project_meta = project_meta
        self.annotation_info = annotation_info
        self.kwargs = kwargs

        self._reports = []

    @property
    def reports(self) -> List[str]:
        return self._reports

    def run(self) -> List[str]:
        # Iterate over subclasses of BaseCase and run them.
        for case in BaseCase.__subclasses__():
            sly.logger.debug("Running test case %s...", case.__name__)
            if not case.is_enabled():
                sly.logger.debug("Case %s is disabled, skipping...", case.__name__)
                continue
            current_case = case(
                project_info=self.project_info,
                project_meta=self.project_meta,
                annotation_info=self.annotation_info,
                **self.kwargs,
            )
            case_report = current_case.run()
            if case_report is not None:
                self._reports.append(case_report)

        sly.logger.info("All test cases were run.")
        return self.reports
