from collections import defaultdict
from typing import Tuple

import supervisely as sly
from supervisely.app.widgets import Card

import src.globals as g
from src.cache import get_annotation_and_meta
from src.test import AllObjectsCase, AverageLabelAreaCase, NoObjectsCase, Test

card = Card("Hello, world!")


app = sly.Application(layout=card)


# region list of checks
# 1. Check if annotaion on image does not contain any objects.
# 2. Check if annotation on image does not contain all objects from the project meta.

# endregion


@app.event(sly.Event.JobEntity.StatusChanged)
@sly.timeit
def job_status_changed(api: sly.Api, event: sly.Event.JobEntity.StatusChanged):
    # If job status is not "done", skip the event.
    if not event.job_entity_status == "done":
        return

    annotation, project_meta = get_annotation_and_meta(event.image_id, event.project_id)
    sly.logger.debug("Annotation for image_id=%s was obtained.", event.image_id)

    test = Test(
        [NoObjectsCase, AllObjectsCase, AverageLabelAreaCase], project_meta, annotation
    )
    test.run()
