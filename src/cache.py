from collections import defaultdict
from typing import Tuple

import supervisely as sly

import src.globals as g
from src.issues import get_or_create_issue

# region temporary caching
# ? Implement effective caching later.
project_meta_cache = defaultdict(lambda: None)  # project_id -> sly.ProjectMeta
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


@sly.timeit
def get_annotation_and_meta(
    image_id: int, project_id: int
) -> Tuple[sly.Annotation, sly.ProjectMeta]:
    project_meta = get_project_meta(project_id)
    ann_json = g.spawn_api.annotation.download_json(
        image_id, force_metadata_for_links=False
    )
    sly.logger.debug("Annotation JSON for image_id=%s was downloaded.", image_id)

    try:
        ann = sly.Annotation.from_json(ann_json, project_meta)
        # return sly.Annotation.from_json(ann_json, project_meta), project_meta
    except Exception:  # TODO: Specify exception.
        project_meta = get_project_meta(project_id, force=True)
        ann = sly.Annotation.from_json(ann_json, project_meta)

    ann = ann.clone(
        image_id=image_id
    )  # TODO: Fix the issue, when image_id is not available in sly.Annotation instance.
    return ann, project_meta


def get_issued_id(issue_name: str) -> int:
    if issue_name not in issues_cache:
        issues_cache[issue_name] = get_or_create_issue(issue_name)
    return issues_cache[issue_name]
