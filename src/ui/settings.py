from supervisely.app.widgets import (
    Card,
    Container,
    Flexbox,
    InputNumber,
    Progress,
    Switch,
    Text,
)

no_objects_case_switch = Switch(switched=True)
no_objects_case_text = Text("No objects on the image")
no_objects_case_flexbox = Flexbox([no_objects_case_switch, no_objects_case_text])

all_objects_case_switch = Switch(switched=True)
all_objects_case_text = Text("Objects of all classes are present on the image")
all_objects_case_flexbox = Flexbox([all_objects_case_switch, all_objects_case_text])

average_label_area_case_switch = Switch(switched=True)
average_label_area_case_text = Text("Area of label differs from average area")
average_label_area_case_flexbox = Flexbox(
    [average_label_area_case_switch, average_label_area_case_text]
)

average_label_area_case_input = InputNumber(value=0.2, min=0.0, max=1.0, step=0.1)
average_label_area_case_container = Container(
    [average_label_area_case_flexbox, average_label_area_case_input]
)

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

progress_bar = Progress()


card = Card(
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


def dummy(*args, **kwargs):
    pass


no_objects_case_switch.value_changed(dummy)
all_objects_case_switch.value_changed(dummy)
average_label_area_case_switch.value_changed(dummy)
average_number_of_class_labels_case_switch.value_changed(dummy)

average_label_area_case_input.value_changed(dummy)
average_number_of_class_labels_case_input.value_changed(dummy)
