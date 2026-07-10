"""App entry point."""

import reflex as rx
from .layout import index

app = rx.App()
app.add_page(index, route="/", title="Product Dashboard")
