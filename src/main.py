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

    # Obtaining actual AnnotationInfo for the image.
    annotation_info = g.spawn_api.annotation.download(
        event.image_id, force_metadata_for_links=False
    )

    # Retrieving project meta and project info from cache.
    project_meta = Cache().get_project_meta(event.project_id)
    project_info = Cache().get_project_info(event.project_id)

    # Creating Test object and running the test.
    test = Test(
        project_info,
        project_meta,
        annotation_info,
        dataset_id=event.dataset_id,
        image_id=event.image_id,
    )
    # TODO: Save reports to the instance of the Test class.
    # And obtain them to show in notification.
    result = test.run()

    add_failed_tests_to_cache = True  # TODO: Obtain this from the settings in the UI.

    if not result:
        sly.logger.info("At least one test failed.")

        # 1. Show notification in the labeling tool.
        # 2. Reject the image in the labeling job.

        for message in test.reports:  # TODO: Implement this in the Test class.
            # Show separate notifications for each failed test with detailed information.
            g.spawn_api.img_ann_tool.show_notification(
                event.session_id,
                message=message,
                notification_type="error",
            )

        reject_images = True  # TODO: Obtain this from the settings in the UI.
        if reject_images:
            g.spawn_api.labeling_job.set_entity_review_status(
                event.job_id, event.image_id, status="rejected"
            )

        if not add_failed_tests_to_cache:
            return

    # Save annotation info to cache only after the test is run
    # to avoid using current annotation info parameters in average calculations.
    # Also, cache is updated only if all tests passed or if the user decided to cache failed tests.
    Cache().update_cached_annotation_info(
        event.project_id, event.image_id, annotation_info
    )
