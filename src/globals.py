import os

import supervisely as sly
import supervisely.app.development as sly_app_development
from dotenv import load_dotenv

if sly.is_development():
    load_dotenv("local.env")
    team_id = sly.env.team_id()
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    sly_app_development.supervisely_vpn_network(action="up")
    sly_app_development.create_debug_task(team_id, update_status=True)

team_id = sly.env.team_id()
workspace_id = sly.env.workspace_id()

api: sly.Api = sly.Api.from_env()

sly.logger.debug(
    "API instance created for team_id=%s, workspace_id=%s", team_id, workspace_id
)
