from collections import defaultdict

import supervisely as sly
from supervisely.api.annotation_api import AnnotationInfo
from supervisely.app.singleton import Singleton

import src.globals as g
from src.issues import get_or_create_issue


class Cache(metaclass=Singleton):
    # project_id -> sly.ProjectMeta
    project_meta = defaultdict(lambda: None)

    # project_id -> sly.ProjectInfo
    project_info = defaultdict(lambda: None)

    # project_id -> image_id -> AnnotationInfo
    annotation_infos = defaultdict(lambda: defaultdict(lambda: None))

    # class_name -> [sly.Label]
    class_labels = defaultdict(list)

    # issue_name -> issue_id
    issues = {}

    @sly.timeit
    def cache_annotation_infos(
        self, project_id: int, force: bool = False, only_labelled: bool = True
    ):
        if project_id not in self.annotation_infos or force:
            datasets = g.spawn_api.dataset.get_list(project_id)
            for dataset in datasets:
                filters = None
                if only_labelled:
                    # We do not need unlabelled images for the tests.
                    # Otherwise on huge datasetets, caching will take too long.
                    filters = [
                        {
                            "type": "objects_class",
                            "data": {
                                "from": 1,
                                "to": 9999,
                                "include": True,
                                "classId": None,
                            },
                        }
                    ]
                image_infos = g.spawn_api.image.get_list(dataset.id, filters=filters)
                image_ids = [image_info.id for image_info in image_infos]

                annotation_infos = g.spawn_api.annotation.download_batch(
                    dataset.id, image_ids, force_metadata_for_links=False
                )

                for annotation_info in annotation_infos:
                    self.annotation_infos[dataset.project_id][
                        annotation_info.image_id
                    ] = annotation_info  # type: ignore

            sly.logger.debug(
                "Annotation infos for project_id=%s were cached.", project_id
            )
        else:
            sly.logger.debug(
                "Annotation infos for project_id=%s were already cached.", project_id
            )

    def update_cached_annotation_info(
        self, project_id: int, image_id: int, annotation_info: AnnotationInfo
    ):
        self.annotation_infos[project_id][image_id] = annotation_info  # type: ignore
        sly.logger.debug(
            "Annotation info for project_id=%s and image_id=%s was updated.",
            project_id,
            image_id,
        )

    def get_project_meta(self, project_id: int, force: bool = False) -> sly.ProjectMeta:
        if project_id not in self.project_meta or force:
            self.project_meta[project_id] = sly.ProjectMeta.from_json(  # type: ignore
                g.spawn_api.project.get_meta(project_id)
            )
            sly.logger.debug("Project meta for project_id=%s was updated.", project_id)
        return self.project_meta[project_id]  # type: ignore

    def get_project_info(self, project_id: int) -> sly.ProjectInfo:
        if project_id not in self.project_info:
            self.project_info[project_id] = g.spawn_api.project.get_info_by_id(  # type: ignore
                project_id
            )
            sly.logger.debug("Project info for project_id=%s was obtained.", project_id)
        return self.project_info[project_id]  # type: ignore

    def get_annotation(
        self,
        annotation_info: AnnotationInfo,
        project_meta: sly.ProjectMeta,
        project_info: sly.ProjectInfo,
    ) -> sly.Annotation:
        try:
            return sly.Annotation.from_json(annotation_info.annotation, project_meta)
        except RuntimeError:
            project_meta = self.get_project_meta(project_info.id, force=True)
            return sly.Annotation.from_json(annotation_info.annotation, project_meta)

    def get_issued_id(self, issue_name: str) -> int:
        if issue_name not in self.issues:
            self.issues[issue_name] = get_or_create_issue(issue_name)
        return self.issues[issue_name]
