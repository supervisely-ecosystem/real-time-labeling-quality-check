from collections import defaultdict
from typing import List

import supervisely as sly
from supervisely.api.annotation_api import AnnotationInfo
from supervisely.app.singleton import Singleton

import src.globals as g
from src.issues import get_or_create_issue
from src.ui.settings import progress_bar


class Cache(metaclass=Singleton):
    # project_id -> sly.ProjectMeta
    project_meta = defaultdict(lambda: None)

    # project_id -> sly.ProjectInfo
    project_info = defaultdict(lambda: None)

    # project_id -> image_id -> AnnotationInfo
    annotation_infos = defaultdict(lambda: defaultdict(lambda: None))

    # issue_name -> issue_id
    issues = {}

    # project_id -> class_name -> average number of labels per image
    class_average_labels = defaultdict(lambda: defaultdict(lambda: None))

    @sly.timeit
    def cache_annotation_infos(
        self, project_id: int, force: bool = False, only_labelled: bool = True
    ):
        if project_id not in self.annotation_infos or force:
            datasets = g.spawn_api.dataset.get_list(project_id)
            for dataset in datasets:
                image_infos = g.spawn_api.image.get_list(
                    dataset.id, only_labelled=only_labelled
                )
                image_ids = [image_info.id for image_info in image_infos]

                with progress_bar(
                    message="Caching annotations...", total=len(image_ids)
                ) as pcb:

                    def progress_cb(to_update: int):
                        pcb.update(to_update)

                    annotation_infos = g.spawn_api.annotation.download_batch(
                        dataset.id,
                        image_ids,
                        force_metadata_for_links=False,
                        progress_cb=progress_cb,
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

    def get_annotations(
        self,
        annotation_infos: List[AnnotationInfo],
        project_meta: sly.ProjectMeta,
        project_info: sly.ProjectInfo,
    ) -> List[sly.Annotation]:
        return [
            self.get_annotation(annotation_info, project_meta, project_info)
            for annotation_info in annotation_infos
        ]

    def get_issued_id(self, issue_name: str) -> int:
        if issue_name not in self.issues:
            self.issues[issue_name] = get_or_create_issue(issue_name)
        return self.issues[issue_name]

    @sly.timeit
    def get_labels_by_class(self, project_id: int, class_name: str) -> List[sly.Label]:
        annotation_infos = self.annotation_infos[project_id]
        project_meta = self.get_project_meta(project_id)

        annotations = self.get_annotations(
            list(annotation_infos.values()), project_meta, self.project_info[project_id]  # type: ignore
        )

        labels = []
        for annotation in annotations:
            for label in annotation.labels:
                if label.obj_class.name == class_name:
                    labels.append(label)

        return labels

    @sly.timeit
    def get_average_number_of_class_labels(self, project_id: int, class_name: str):
        # ! Warning this method calculates average number of labels for class_name
        # ! even if there are no labels for this class in the image.
        # E.g. number of labels / number of images.
        # Which is incorrect, we should only calculate average number of labels
        # per class for images that have labels for this class on them.
        # ! Reimplement this method to calculate average number of labels correctly.
        # E.g. implement method to get number of images with labels for class_name.
        if class_name not in self.class_average_labels[project_id]:
            labels = self.get_labels_by_class(project_id, class_name)
            average_labels = len(labels) / len(self.annotation_infos[project_id])
            self.class_average_labels[project_id][class_name] = average_labels  # type: ignore
            sly.logger.debug(
                "Average number of labels for class %s was calculated: %s.",
                class_name,
                average_labels,
            )
        return self.class_average_labels[project_id][class_name]
