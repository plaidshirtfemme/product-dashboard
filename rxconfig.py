import reflex as rx
from reflex_base.plugins.sitemap import SitemapPlugin
from reflex_components_radix.plugin import RadixThemesPlugin

config = rx.Config(
    app_name="dash_app",
    disable_plugins=[SitemapPlugin],
    plugins=[
        RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                accent_color="teal",
                gray_color="slate",
                radius="medium",
                scaling="100%",
                has_background=True,
            )
        )
    ],
)
