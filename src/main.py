import supervisely as sly
from supervisely.app.widgets import Card

import src.globals as g

card = Card("Hello, world!")


app = sly.Application(layout=card)
