from collections import defaultdict
from typing import Tuple

import supervisely as sly
from supervisely.app.widgets import Card

import src.globals as g
from src.test import AllObjectsCase, NoObjectsCase, Test

card = Card("Hello, world!")


app = sly.Application(layout=card)

# region temporary caching
# ? Implement effective caching later.
project_meta_cache = defaultdict(lambda: None)  # project_id -> sly.ProjectMeta
# endregion

# region list of checks
# 1. Check if annotaion on image does not contain any objects.
# 2. Check if annotation on image does not contain all objects from the project meta.

# endregion


def get_project_meta(project_id: int, force: bool = False) -> sly.ProjectMeta:
    if project_meta_cache[project_id] is None or force:
        project_meta_cache[project_id] = sly.ProjectMeta.from_json(
            g.spawn_api.project.get_meta(project_id)
        )
        sly.logger.debug("Project meta for project_id=%s was updated.", project_id)
    return project_meta_cache[project_id]


def get_annotation_and_meta(
    image_id: int, project_id: int
) -> Tuple[sly.Annotation, sly.ProjectMeta]:
    project_meta = get_project_meta(project_id)
    ann_json = g.spawn_api.annotation.download_json(
        image_id, force_metadata_for_links=False
    )
    sly.logger.debug("Annotation JSON for image_id=%s was downloaded.", image_id)

    try:
        return sly.Annotation.from_json(ann_json, project_meta), project_meta
    except Exception:  # TODO: Specify exception.
        project_meta = get_project_meta(project_id, force=True)
        return sly.Annotation.from_json(ann_json, project_meta), project_meta


@app.event(sly.Event.JobEntity.StatusChanged)
def job_status_changed(api: sly.Api, event: sly.Event.JobEntity.StatusChanged):
    # If job status is not "done", skip the event.
    if not event.job_entity_status == "done":
        return

    annotation, project_meta = get_annotation_and_meta(event.image_id, event.project_id)
    sly.logger.debug("Annotation for image_id=%s was obtained.", event.image_id)

    test = Test([NoObjectsCase, AllObjectsCase], project_meta, annotation)
    test.run()
