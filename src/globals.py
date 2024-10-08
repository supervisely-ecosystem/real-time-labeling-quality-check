import os

import supervisely as sly
import supervisely.app.development as sly_app_development
from dotenv import load_dotenv

DEFAULT_THRESHOLD = 0.2

if sly.is_development():
    load_dotenv("local.env")
    spawn_team_id = sly.env.team_id()
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    sly_app_development.supervisely_vpn_network(action="up")
    sly_app_development.create_debug_task(spawn_team_id, update_status=True)

spawn_team_id = sly.env.team_id()
spawn_workspace_id = sly.env.workspace_id()

spawn_api = sly.Api.from_env()

sly.logger.debug(
    "Spawn API instance created for team_id=%s, workspace_id=%s",
    spawn_team_id,
    spawn_workspace_id,
)

# region Cases
no_objects_case_enabled = True
all_objects_case_enabled = True

average_label_area_case_enabled = True
average_label_area_case_theshold = DEFAULT_THRESHOLD
average_number_of_class_labels_case_enabled = True
average_number_of_class_labels_case_theshold = DEFAULT_THRESHOLD
# endregion


# region Settings
create_issues: bool = False
reject_images: bool = False
use_failed_images: bool = False
# endregion
