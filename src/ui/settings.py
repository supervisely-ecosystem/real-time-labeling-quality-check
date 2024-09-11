from supervisely.app.widgets import (
    Card,
    Container,
    Flexbox,
    InputNumber,
    Progress,
    Switch,
    Text,
)

from src.utils import dummy

# region NoObjectsCase
no_objects_case_switch = Switch(switched=True)
no_objects_case_text = Text("No objects on the image")
no_objects_case_flexbox = Flexbox([no_objects_case_switch, no_objects_case_text])

no_objects_case_switch.value_changed(dummy)
# endregion

# region AllObjectsCase
all_objects_case_switch = Switch(switched=True)
all_objects_case_text = Text("Objects of all classes are present on the image")
all_objects_case_flexbox = Flexbox([all_objects_case_switch, all_objects_case_text])

all_objects_case_switch.value_changed(dummy)
# endregion

# region AverageLabelAreaCase
average_label_area_case_switch = Switch(switched=True)
average_label_area_case_text = Text("Area of label differs from average area")
average_label_area_case_flexbox = Flexbox(
    [average_label_area_case_switch, average_label_area_case_text]
)

average_label_area_case_input = InputNumber(value=0.2, min=0.0, max=1.0, step=0.1)
average_label_area_case_container = Container(
    [average_label_area_case_flexbox, average_label_area_case_input]
)


@average_label_area_case_switch.value_changed
def on_average_label_area_case_switch_changed(is_on: bool) -> None:
    """Callback for the average_label_area_case_switch.
    Hide or show the average_label_area_case_input based on the switch state.

    :param is_on: The state of the switch.
    :type is_on: bool
    """
    if is_on:
        average_label_area_case_input.show()
    else:
        average_label_area_case_input.hide()


average_label_area_case_input.value_changed(dummy)
# endregion

# region AverageNumberOfClassLabelsCase
average_number_of_class_labels_case_switch = Switch(switched=True)
average_number_of_class_labels_case_text = Text(
    "Number of labels for class differs from average"
)
average_number_of_class_labels_case_flexbox = Flexbox(
    [
        average_number_of_class_labels_case_switch,
        average_number_of_class_labels_case_text,
    ]
)
average_number_of_class_labels_case_input = InputNumber(
    value=0.2, min=0.0, max=1.0, step=0.1
)
average_number_of_class_labels_case_container = Container(
    [
        average_number_of_class_labels_case_flexbox,
        average_number_of_class_labels_case_input,
    ]
)


@average_number_of_class_labels_case_switch.value_changed
def on_average_number_of_class_labels_case_switch_changed(is_on: bool) -> None:
    """Callback for the average_number_of_class_labels_case_switch.
    Hide or show the average_number_of_class_labels_case_input based on the switch state.

    :param is_on: The state of the switch.
    :type is_on: bool
    """
    if is_on:
        average_number_of_class_labels_case_input.show()
    else:
        average_number_of_class_labels_case_input.hide()


average_number_of_class_labels_case_input.value_changed(dummy)
# endregion

# Progress bar for showing caching progress.
progress_bar = Progress()

# Card with all tests.
tests_card = Card(
    "Labeling Quality Check",
    description="List of checks to be performed on the image",
    content=Container(
        [
            no_objects_case_flexbox,
            all_objects_case_flexbox,
            average_label_area_case_container,
            average_number_of_class_labels_case_container,
            progress_bar,
        ]
    ),
)

# region CreateIssuesSwitch
create_issues_switch = Switch(switched=False)
create_issues_text = Text("Create issues for failed tests")
create_issues_flexbox = Flexbox([create_issues_switch, create_issues_text])

create_issues_switch.value_changed(dummy)
# endregion

# region RejectImagesSwitch
reject_images_switch = Switch(switched=False)
reject_images_text = Text("Reject images with failed tests")
reject_images_flexbox = Flexbox([reject_images_switch, reject_images_text])

reject_images_switch.value_changed(dummy)
# endregion

# region UseFailedImagesSwitch
use_failed_images_switch = Switch(switched=False)
use_failed_images_text = Text("Include failed images in statistics")
use_failed_images_flexbox = Flexbox([use_failed_images_switch, use_failed_images_text])

use_failed_images_switch.value_changed(dummy)
# endregion

# Card with settings.
settings_card = Card(
    "Settings",
    description="Settings for the labeling quality check",
    content=Container(
        [
            create_issues_flexbox,
            reject_images_flexbox,
            use_failed_images_flexbox,
        ]
    ),
    collapsable=True,
)
settings_card.collapse()

# Container with all cards, which will be used as a layout for the application.
container = Container([tests_card, settings_card])
