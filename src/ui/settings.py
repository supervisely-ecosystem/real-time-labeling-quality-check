from supervisely.app.widgets import Card, Container, Flexbox, InputNumber, Switch, Text

no_objects_case_switch = Switch(switched=True, widget_id="NoObjectsCase")
no_objects_case_text = Text("No objects on the image")
no_objects_case_flexbox = Flexbox([no_objects_case_switch, no_objects_case_text])

all_objects_case_switch = Switch(switched=True, widget_id="AllObjectsCase")
all_objects_case_text = Text("Objects of all classes are present on the image")
all_objects_case_flexbox = Flexbox([all_objects_case_switch, all_objects_case_text])

average_label_area_case_switch = Switch(switched=True, widget_id="AverageLabelAreaCase")
average_label_area_case_text = Text("Area of label differs from average area")
average_label_area_case_flexbox = Flexbox(
    [average_label_area_case_switch, average_label_area_case_text]
)

average_label_area_case_input = InputNumber(
    value=0.2, min=0.0, max=1.0, step=0.1, widget_id="AverageLabelAreaCase_threshold"
)
average_label_area_case_container = Container(
    [average_label_area_case_flexbox, average_label_area_case_input]
)

card = Card(
    "Labeling Quality Check",
    description="List of checks to be performed on the image",
    content=Container(
        [
            no_objects_case_flexbox,
            all_objects_case_flexbox,
            average_label_area_case_container,
        ]
    ),
)


def dummy(*args, **kwargs):
    pass


no_objects_case_switch.value_changed(dummy)
all_objects_case_switch.value_changed(dummy)
average_label_area_case_switch.value_changed(dummy)

average_label_area_case_input.value_changed(dummy)
