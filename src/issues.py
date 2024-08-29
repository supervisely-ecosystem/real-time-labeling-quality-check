from typing import Tuple

import supervisely as sly

import src.globals as g


def get_or_create_issue(issue_name: str) -> int:
    all_issues = g.spawn_api.issues.get_list(team_id=g.spawn_team_id)
    for issue in all_issues:
        if issue.name == issue_name:
            sly.logger.debug(
                "Issue with name %s was found. Issue ID: %s", issue_name, issue.id
            )
            return issue.id

    sly.logger.debug(
        "Issue with name %s was not found. Creating a new issue.", issue_name
    )

    issue_id = g.spawn_api.issues.add(
        g.spawn_team_id, issue_name
    ).id  # ? Add spawner user as assignee?

    return issue_id


def get_top_and_left(label: sly.Label) -> Tuple[int, int]:
    bbox: sly.Rectangle = label.geometry.to_bbox()
    return bbox.top, bbox.left
