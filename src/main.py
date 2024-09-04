import supervisely as sly

import src.globals as g
from src.cache import Cache
from src.test import Test
from src.ui.settings import card

app = sly.Application(layout=card)


@app.event(sly.Event.JobEntity.StatusChanged)  # type: ignore
@sly.timeit
def job_status_changed(api: sly.Api, event: sly.Event.JobEntity.StatusChanged):
    # If job status is not "done", skip the event.
    if not event.job_entity_status == "done":
        sly.logger.debug("Job status is not 'done'. Skipping the event.")
        return

    Cache().cache_annotation_infos(event.project_id)

    annotation_info = g.spawn_api.annotation.download(
        event.image_id, force_metadata_for_links=False
    )

    project_meta = Cache().get_project_meta(event.project_id)
    project_info = Cache().get_project_info(event.project_id)

    test = Test(project_info, project_meta, annotation_info)
    test.run()

    # Save annotation info to cache only after the test is run
    # to avoid using current annotation info parameters in average calculations.
    Cache().update_cached_annotation_info(
        event.project_id, event.image_id, annotation_info
    )
