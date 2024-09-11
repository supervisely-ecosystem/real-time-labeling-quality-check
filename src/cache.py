from collections import defaultdict
from typing import Dict, List

import supervisely as sly
from supervisely.api.annotation_api import AnnotationInfo
from supervisely.app.singleton import Singleton

import src.globals as g
from src.issues import get_or_create_issue
from src.ui.settings import progress_bar


class Cache(metaclass=Singleton):
    """Cache class for storing the metadata of the project, project info, annotation info,
    and issues. It also contains methods for caching and getting the cached data.

    Properties:
    - project_meta: Metadata of the project.
    - project_info: Information about the project.
    - annotation_infos: Information about the annotations.
    - issues: Issues in the project.

    Methods:
    - cache_annotation_infos: Cache the annotation information.
    - update_cached_annotation_info: Update the cached annotation information.
    - get_project_meta: Get the metadata of the project.
    - get_project_info: Get the information about the project.
    - get_annotation: Get the annotation.
    - get_annotations: Get the annotations.
    - get_issued_id: Get the issue ID.
    - get_labels_by_class: Get the labels by class.
    - get_annotations_for_whole_project: Get the annotations for the whole project.
    - group_annotations_by_class: Group the annotations by class.
    """

    # project_id -> sly.ProjectMeta
    project_meta = defaultdict(lambda: None)

    # project_id -> sly.ProjectInfo
    project_info = defaultdict(lambda: None)

    # project_id -> image_id -> AnnotationInfo
    annotation_infos = defaultdict(lambda: defaultdict(lambda: None))

    # issue_name -> issue_id
    issues = {}

    @sly.timeit
    def cache_annotation_infos(
        self, project_id: int, force: bool = False, only_labelled: bool = True
    ) -> None:
        """Cache the annotation information.

        :param project_id: The ID of the project.
        :type project_id: int
        :param force: Whether to force the caching of the annotation information.
        :type force: bool
        :param only_labelled: Whether to cache only labelled images.
        :type only_labelled: bool
        """
        if project_id not in self.annotation_infos or force:
            # * We do not need to obtain a lsit of datasets, if we need only Image Infos.
            # * But we need dataset IDs to obtain Annotation Infos.
            # ? If those changes will be added to API/SDK, consider removing this iteration
            # ? for speeding up the process.
            datasets = g.spawn_api.dataset.get_list(project_id)
            for dataset in datasets:
                image_infos = g.spawn_api.image.get_list(
                    dataset.id, only_labelled=only_labelled
                )
                image_ids = [image_info.id for image_info in image_infos]

                with progress_bar(
                    message="Caching annotations...", total=len(image_ids)
                ) as pcb:

                    def progress_cb(to_update: int) -> None:
                        """Progress callback for the progress bar,
                        required to update the progress bar in the UI.

                        :param to_update: The number of images to update.
                        :type to_update: int
                        """
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
    ) -> None:
        """Update Annotation Info in the cache with the new Annotation Info.

        :param project_id: The ID of the project.
        :type project_id: int
        :param image_id: The ID of the image.
        :type image_id: int
        :param annotation_info: The new Annotation Info.
        :type annotation_info: AnnotationInfo
        """
        self.annotation_infos[project_id][image_id] = annotation_info  # type: ignore
        sly.logger.debug(
            "Annotation info for project_id=%s and image_id=%s was updated.",
            project_id,
            image_id,
        )

    def get_project_meta(self, project_id: int, force: bool = False) -> sly.ProjectMeta:
        """Get the metadata of the project from the cache (or from the server if not cached).

        :param project_id: The ID of the project.
        :type project_id: int
        :param force: Whether to force the obtaining of the metadata.
        :type force: bool
        :return: The metadata of the project.
        :rtype: sly.ProjectMeta
        """
        if project_id not in self.project_meta or force:
            self.project_meta[project_id] = sly.ProjectMeta.from_json(  # type: ignore
                g.spawn_api.project.get_meta(project_id)
            )
            sly.logger.debug("Project meta for project_id=%s was updated.", project_id)
        return self.project_meta[project_id]  # type: ignore

    def get_project_info(self, project_id: int) -> sly.ProjectInfo:
        """Get the information about the project from the cache (or from the server if not cached).

        :param project_id: The ID of the project.
        :type project_id: int
        :return: The information about the project.
        :rtype: sly.ProjectInfo
        """
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
        """Get the annotation from the annotation information.
        If can not retrieve the annotation from the given Project Meta, try to get it from the server.

        :param annotation_info: The annotation information.
        :type annotation_info: AnnotationInfo
        :param project_meta: The metadata of the project.
        :type project_meta: sly.ProjectMeta
        :param project_info: The information about the project.
        :type project_info: sly.ProjectInfo
        :return: The annotation.
        :rtype: sly.Annotation
        """
        try:
            return sly.Annotation.from_json(annotation_info.annotation, project_meta)
        except Exception:
            # In case of an error, try to get the new project meta and annotation info
            # from the server and return the annotation.
            project_meta = self.get_project_meta(project_info.id, force=True)
            new_annotation_info = g.spawn_api.annotation.download(
                annotation_info.image_id, force_metadata_for_links=False
            )
            sly.logger.info(
                "Obtained new Project Meta and new Annotation Info for project_id=%s and image_id=%s",
                project_info.id,
                annotation_info.image_id,
            )

            return sly.Annotation.from_json(
                new_annotation_info.annotation, project_meta
            )

    @sly.timeit
    def get_annotations(
        self,
        annotation_infos: List[AnnotationInfo],
        project_meta: sly.ProjectMeta,
        project_info: sly.ProjectInfo,
    ) -> List[sly.Annotation]:
        """Get the annotations from the annotation information.

        :param annotation_infos: The annotation information.
        :type annotation_infos: List[AnnotationInfo]
        :param project_meta: The metadata of the project.
        :type project_meta: sly.ProjectMeta
        :param project_info: The information about the project.
        :type project_info: sly.ProjectInfo
        :return: The annotations.
        :rtype: List[sly.Annotation]
        """
        return [
            self.get_annotation(annotation_info, project_meta, project_info)
            for annotation_info in annotation_infos
        ]

    def get_issued_id(self, issue_name: str) -> int:
        """Get the issue ID from the issue name.

        :param issue_name: The name of the issue.
        :type issue_name: str
        :return: The issue ID.
        :rtype: int
        """
        if issue_name not in self.issues:
            self.issues[issue_name] = get_or_create_issue(issue_name)
        return self.issues[issue_name]

    @sly.timeit
    def get_labels_by_class(self, project_id: int, class_name: str) -> List[sly.Label]:
        """Get the labels by class.

        :param project_id: The ID of the project.
        :type project_id: int
        :param class_name: The name of the class.
        :type class_name: str
        :return: The labels.
        :rtype: List[sly.Label]
        """
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
    def get_annotations_for_whole_project(
        self, project_id: int
    ) -> List[sly.Annotation]:
        """Get the annotations for the whole project.

        :param project_id: The ID of the project.
        :type project_id: int
        :return: The annotations.
        :rtype: List[sly.Annotation]
        """
        annotation_infos = self.annotation_infos[project_id]
        project_meta = self.get_project_meta(project_id)

        return self.get_annotations(
            list(annotation_infos.values()), project_meta, self.project_info[project_id]  # type: ignore
        )

    @sly.timeit
    def group_annotations_by_class(
        self, project_id: int
    ) -> Dict[str, List[sly.Annotation]]:
        """Group the annotations by class.
        Return the dictionary with the class name as the key and the list of annotations as the value.

        :param project_id: The ID of the project.
        :type project_id: int
        :return: The grouped annotations.
        :rtype: Dict[str, List[sly.Annotation]]
        """
        annotations = self.get_annotations_for_whole_project(project_id)

        grouped_annotations = defaultdict(list)
        for annotation in annotations:
            for label in annotation.labels:
                grouped_annotations[label.obj_class.name].append(annotation)

        return grouped_annotations
