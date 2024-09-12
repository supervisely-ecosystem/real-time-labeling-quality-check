from typing import List, Optional, Union

import supervisely as sly
from supervisely.api.annotation_api import AnnotationInfo
from supervisely.imaging.image import get_new_labeling_tool_url

import src.globals as g
from src.cache import Cache
from src.issues import get_top_and_left


class BaseCase:
    """Base class for all test cases. It contains the logic for running the test and
    creating an issue, if the test fails. The exact logic of the test should be
    implemented in the run_result method.

    :param project_info: Information about the project.
    :type project_info: sly.ProjectInfo
    :param project_meta: Metadata of the project.
    :type project_meta: sly.ProjectMeta
    :param annotation_info: Information about the annotation.
    :type annotation_info: AnnotationInfo
    :param kwargs: Additional keyword arguments.
    :type kwargs: Any

    Properties:
    - report: Report of the test.
    - failed_labels: List of labels that failed the test.

    Methods:
    - run: Run the test.
    - create_issue: Create an issue for the test.
    - create_subissues: Create subissues for the test.
    - add_link_to_report: Add a link to the image to the report.
    - add_meta_to_report: Add metadata to the report.
    - run_result: Run the test and return the result.
    - is_enabled: Check if the test is enabled.
    - get_threshold: Get the threshold for the test.
    """

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
        """Report of the test. Should be set in the run_result method.

        :return: Report of the test.
        :rtype: Union[str, None]
        """
        return self._report

    @report.setter
    def report(self, value: str) -> None:
        """Set the report of the test.

        :param value: Report of the test.
        :type value: str
        """
        self._report = value

    @property
    def failed_labels(self) -> List[sly.Label]:
        """List of labels that failed the test.

        :return: List of labels that failed the test.
        :rtype: List[sly.Label]
        """
        return self._failed_labels

    def run_result(self) -> bool:
        """Run the test and return the result.

        :return: True if the test passed, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError()

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if the test is enabled.

        :return: True if the test is enabled, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError()

    @classmethod
    def get_threshold(cls) -> Optional[float]:
        """Get the threshold for the test.

        :return: The threshold for the test.
        :rtype: Optional[float]
        """
        raise NotImplementedError()

    @sly.timeit
    def run(self) -> Optional[str]:
        """Run the test. Return the report of the test.

        :return: The report of the test.
        :rtype: Optional[str]
        """
        if self.run_result():
            sly.logger.info(
                "[SUCCESS] Test for case %s passed.", self.__class__.__name__
            )
        else:
            sly.logger.info(
                "[FAILED ] Test for case %s failed.", self.__class__.__name__
            )

            # If the test failed, create an issue.
            self.create_issue()

        return self.report

    @sly.timeit
    def create_issue(self) -> None:
        """Create an issue and subissues for the test."""
        # Get the issue ID from the cache.
        issue_name = f"Annotation Quality Check: {self.project_info.name}"
        issue_id = Cache().get_issued_id(issue_name)

        # Create issue only if the switch is on and if the report is not empty.
        if self.report is not None and g.create_issues:
            # Add a metadata to the report.
            report = self.add_meta_to_report(self.report)

            # Add a link to the image to the report.
            report = self.add_link_to_report(report)

            # Add comment with detailed report to the issue.
            g.spawn_api.issues.add_comment(issue_id, report)
            sly.logger.debug("Comment was added to issue %s.", issue_id)

            # Create subissues for the failed labels.
            # NOTE: This only works for the cases, which related to specific labels.
            # And it does not work for cases, which related to the whole image or annotation.
            self.create_subissues(issue_id, self.failed_labels)

    @sly.timeit
    def create_subissues(self, issue_id: int, labels: List[sly.Label]) -> None:
        """Create subissues for the test.

        :param issue_id: The ID of the issue.
        :type issue_id: int
        :param labels: List of labels that failed the test.
        :type labels: List[sly.Label]
        """
        # Iterate over the failed labels and create subissues for them.
        for label in labels:
            # Get the top and left coordinates of the label to add subissue marker.
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
        """Modify the report by adding a link to the image.

        :param report: The report to modify.
        :type report: str
        :return: The modified report.
        :rtype: str
        """
        try:
            url = get_new_labeling_tool_url(**self.kwargs)
        except Exception as e:
            sly.logger.warning("Failed to get the link to the image: %s", e)
            return report

        return f"{report}\n\n [Link to the image]({url})"

    def add_meta_to_report(self, report: str) -> str:
        """Modify the report by adding metadata to it.

        :param report: The report to modify.
        :type report: str
        :return: The modified report.
        :rtype: str
        """
        meta = (
            f"Image ID: {self.annotation_info.image_id}\n\n"
            f"Image Name: {self.annotation_info.image_name}\n\n"
            f"Project ID: {self.project_info.id}\n\n"
            f"Project Name: {self.project_info.name}\n\n"
        )

        return f"{report}\n\n{meta}"


class Test:
    """Class for running test using a list of test cases.
    One instance of the test class is created for each image.

    :param project_info: Information about the project.
    :type project_info: sly.ProjectInfo
    :param project_meta: Metadata of the project.
    :type project_meta: sly.ProjectMeta
    :param annotation_info: Information about the annotation.
    :type annotation_info: AnnotationInfo
    :param kwargs: Additional keyword arguments.
    :type kwargs: Any

    Properties:
    - reports: List of reports of the test cases.

    Methods:
    - run: Run the test.
    """

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
        """List of reports of the test cases.

        :return: List of reports of the test cases.
        :rtype: List[str]
        """
        return self._reports

    @sly.timeit
    def run(self) -> List[str]:
        """Run the test.

        :return: List of reports of the test cases.
        :rtype: List[str]
        """
        # Iterate over subclasses of BaseCase and run them.
        for case in BaseCase.__subclasses__():
            sly.logger.debug("Running test case %s...", case.__name__)

            # Check if the case is enabled in the UI.
            if not case.is_enabled():
                sly.logger.debug("Case %s is disabled, skipping...", case.__name__)
                continue

            # Create an instance of the case and run it.
            current_case = case(
                project_info=self.project_info,
                project_meta=self.project_meta,
                annotation_info=self.annotation_info,
                **self.kwargs,
            )
            case_report = current_case.run()

            # If the case contains a report, add it to the list of reports.
            if case_report is not None:
                self._reports.append(case_report)

        sly.logger.info("All test cases were run.")
        return self.reports
