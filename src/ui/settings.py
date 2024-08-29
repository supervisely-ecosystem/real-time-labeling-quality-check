from supervisely.app.widgets import Card, Container, Flexbox, InputNumber, Switch, Text

import src.test as test


def value_changed_switch(self, func):
    route_path = self.get_route_path(Switch.Routes.VALUE_CHANGED)
    server = self._sly_app.get_server()
    self._changes_handled = True

    @server.post(route_path)
    def _click():
        res = self.is_switched()
        func(res, self.widget_id)

    return _click


def value_changed_input(self, func):
    route_path = self.get_route_path(InputNumber.Routes.VALUE_CHANGED)
    server = self._sly_app.get_server()
    self._changes_handled = True

    @server.post(route_path)
    def _click():
        res = self.get_value()
        self._value = res
        func(res, self.widget_id)

    return _click


Switch.value_changed = value_changed_switch
InputNumber.value_changed = value_changed_input


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


def change_case_status(value: bool, widget_id: str) -> None:
    eval(f"test.{widget_id}.set_enabled({value})")


def change_case_threshold(value: float, widget_id: str) -> None:
    class_name = widget_id.split("_")[0]
    eval(f"test.{class_name}.set_threshold({value})")


no_objects_case_switch.value_changed(change_case_status)
all_objects_case_switch.value_changed(change_case_status)
average_label_area_case_switch.value_changed(change_case_status)

average_label_area_case_input.value_changed(change_case_threshold)


# @average_label_area_case_input.value_changed
# def average_label_area_case_input_changed(value: float) -> None:
#     test.AverageLabelAreaCase.set_threshold(value)
