import flet as ft
from database import init_db
from ui import build_app

def main(page: ft.Page):
    # page.title = "Fitness Tracker"
    # page.window_width = 420
    # page.window_height = 780
    # page.theme_mode = ft.ThemeMode.LIGHT

    # init_db()
    # ui = FitnessAppUI(page)
    # ui.build()
    init_db()
    build_app(page)



if __name__ == "__main__":
    ft.app(target=main)