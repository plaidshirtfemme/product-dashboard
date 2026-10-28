"""App entry point."""

import reflex as rx
from .layout import index
from .components.reorderable_table import table_runtime
from .states.ba_sa_state import BaSaState

# table_runtime() — JS перетаскивания/ресайза колонок (DASH-114). Только в head:
# rx.script() внутри дерева компонентов в DOM не попадает.
app = rx.App(head_components=[table_runtime()])
# on_load: конспекты BA/SA перечитываются с диска при каждой загрузке
# страницы — правка .md в Obsidian видна по F5, без перезапуска сервера.
app.add_page(index, route="/", title="Product Dashboard", on_load=BaSaState.load)
