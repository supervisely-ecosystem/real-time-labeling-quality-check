from collections import defaultdict

import supervisely as sly
from supervisely.app.widgets import Card

import src.globals as g
from src.test import NoObjectsCase, Test

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


def get_annotation(image_id: int, project_id: int) -> sly.Annotation:
    project_meta = get_project_meta(project_id)
    ann_json = g.spawn_api.annotation.download_json(
        image_id, force_metadata_for_links=False
    )
    sly.logger.debug("Annotation JSON for image_id=%s was downloaded.", image_id)

    try:
        return sly.Annotation.from_json(ann_json, project_meta)
    except Exception:  # TODO: Specify exception.
        project_meta = get_project_meta(project_id, force=True)
        return sly.Annotation.from_json(ann_json, project_meta)


@app.event(sly.Event.ManualSelected.ImageChanged)
def image_changed(api: sly.Api, event: sly.Event.ManualSelected.ImageChanged):
    # 1. Obtain annotation in JSON format using image_id.
    # 2. If project_meta for the current project is not cached, obtain project_meta from the server.
    # 3. Try to create sly.Annotation object from JSON using project_meta_cache.
    # 4. If there was an error while creating annotation, assume that project_meta_cache is outdated and update it to create annotation again.

    annotation = get_annotation(event.image_id, event.project_id)
    sly.logger.debug("Annotation for image_id=%s was obtained.", event.image_id)

    test = Test([NoObjectsCase], event.project_id, annotation)
    test.run()
