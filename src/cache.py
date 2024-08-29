from collections import defaultdict

import supervisely as sly
from supervisely.api.annotation_api import AnnotationInfo

import src.globals as g
from src.issues import get_or_create_issue

# region temporary caching
# ? Implement effective caching later.
project_meta_cache = defaultdict(lambda: None)  # project_id -> sly.ProjectMeta
project_info_cache = defaultdict(lambda: None)  # project_id -> sly.ProjectInfo
labels_cache = defaultdict(list)  # class_name -> [sly.Label]
issues_cache = {}  # issue_name -> issue_id
# endregion


def get_project_meta(project_id: int, force: bool = False) -> sly.ProjectMeta:
    if project_id not in project_meta_cache or force:
        project_meta_cache[project_id] = sly.ProjectMeta.from_json(
            g.spawn_api.project.get_meta(project_id)
        )
        sly.logger.debug("Project meta for project_id=%s was updated.", project_id)
    return project_meta_cache[project_id]


def get_project_info(project_id: int) -> sly.ProjectInfo:
    if project_id not in project_info_cache:
        project_info_cache[project_id] = g.spawn_api.project.get_info_by_id(project_id)
        sly.logger.debug("Project info for project_id=%s was obtained.", project_id)
    return project_info_cache[project_id]


def get_annotation_info(image_id: int) -> AnnotationInfo:
    annotation_info = g.spawn_api.annotation.download(
        image_id, force_metadata_for_links=False
    )
    return annotation_info


def get_issued_id(issue_name: str) -> int:
    if issue_name not in issues_cache:
        issues_cache[issue_name] = get_or_create_issue(issue_name)
    return issues_cache[issue_name]
