"""App entry point."""

import reflex as rx
from .layout import index
from .components.reorderable_table import table_runtime

# table_runtime() — JS перетаскивания/ресайза колонок (DASH-114). Только в head:
# rx.script() внутри дерева компонентов в DOM не попадает.
app = rx.App(head_components=[table_runtime()])
app.add_page(index, route="/", title="Product Dashboard")
