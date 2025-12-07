from datetime import datetime
from models import list_weights, list_exercises_for_prs, list_muscle_group,list_muscle_exercises
from charts import png_converter
import flet as ft
import json

# Get all muscle groups (unique)
def get_muscle_groups():
    # exercises = list_exercises()
    muscle_groups = list_muscle_group()

    # for ex in exercises:
    #     if ex.get("muscle"):
    #         muscle_groups.add(ex["muscle"])
    
    for mg in muscle_groups:
        png_base_64  =png_converter(mg.get('mg_image'))
        mg["mg_image"] = None          # remove old value
        mg["mg_image"] = png_base_64

    # 'mg_image'

    return list(muscle_groups)

def get_exercises_for_mg(mg_id):
    muscle_exercises = list_muscle_exercises(mg_id)
    return list(muscle_exercises)


# Get PRs for all exercises in a specific muscle group
def get_prs_for_muscle_group(id,muscle_group):

    exercises = list_exercises_for_prs(id)

    prs = {}  # { "Bench Press": {"weight": 90, "date": <date>} }
    for ex in exercises:
        # if ex.get("muscle_group") != muscle_group:
        #     continue
        weight = 0
        name = ex.get("name")
        sets = json.loads(ex["sets_json"])   # convert JSON string → list of dicts

        for s in sets:
            weight = max(weight, s.get("weight", 0))
            
        date = ex.get("date")
        if isinstance(date, str):
            date = datetime.fromisoformat(date).date()

        if name not in prs or weight > prs[name]["weight"]:
            prs[name] = {"weight": weight, "date": date}

    return prs



# def create_searchable_dropdown(page: ft.Page, label: str, options: list, on_change=None, width: int | None = 300):
#     """
#     options: list of (key, text) tuples, e.g. [("1","Chest"), ("2","Back")]
#     Returns: (control, api) where control is an ft.Control you add to page,
#              and api is a small object with .get() and .set(key) methods.
#     """

#     # internal state
#     selected_key = {"value": None}
#     expanded = {"value": False}

#     # display TextField (looks like a dropdown)
#     display = ft.TextField(
#         label=label,
#         read_only=True,
#         width=width,
#         suffix_icon=ft.Icons.ARROW_DROP_DOWN,
#         on_click=lambda e: toggle_dropdown(e),
#     )

#     # search input shown inside dropdown panel
#     search_input = ft.TextField(
#         hint_text="Search...",
#         visible=False,
#         on_change=lambda e: filter_list(e),
#     )

#     # list view for options
#     listview = ft.ListView(expand=True, spacing=4, height=200)

#     # popup/dropdown container (initially hidden)
#     dropdown_panel = ft.Container(
#         content=ft.Column([search_input, listview], spacing=6),
#         visible=False,
#         width=width,
#         padding=8,
#         bgcolor=ft.Colors.SURFACE,
#         border_radius=8,
#         border=ft.border.all(1, ft.Colors.GREY_300),
#     )

#     # main composite control
#     main = ft.Column([display, dropdown_panel], spacing=4)

#     # helper to build list items (do not call .update() here)
#     def build_list(items):
#         listview.controls.clear()
#         for key, text in items:
#             listview.controls.append(
#                 ft.Container(
#                     content=ft.Text(text),
#                     padding=8,
#                     border_radius=6,
#                     ink=True,
#                     on_click=lambda e, k=key, t=text: select_item(k, t),
#                 )
#             )

#     # initial build (no update call)
#     build_list(options)

#     # event handlers
#     def toggle_dropdown(e):
#         expanded["value"] = not expanded["value"]
#         dropdown_panel.visible = expanded["value"]
#         search_input.visible = expanded["value"]
#         if expanded["value"]:
#             # focus search_input when opening (deferred)
#             page.update()
#             # set empty search to show all
#             search_input.value = ""
#             filter_list(None)
#             # focus will work after update
#         display.update()
#         dropdown_panel.update()
#         search_input.update()
#         listview.update()

#     def filter_list(e):
#         q = ""
#         if e is not None:
#             # either TextField on_change event (e.control exists)
#             q = e.control.value.lower()
#         else:
#             q = search_input.value.lower() if search_input.value else ""

#         filtered = [(k, t) for (k, t) in options if q in t.lower()]
#         build_list(filtered)
#         listview.update()

#     def select_item(key, text):
#         selected_key["value"] = key
#         display.value = text
#         # close
#         expanded["value"] = False
#         dropdown_panel.visible = False
#         search_input.visible = False

#         # reflect changes
#         display.update()
#         dropdown_panel.update()
#         listview.update()
#         search_input.update()

#         if on_change:
#             on_change(key)

#     # small API to return to caller
#     class API:
#         @staticmethod
#         def get():
#             return selected_key["value"]

#         @staticmethod
#         def set(k):
#             # find text for key
#             for _k, _t in options:
#                 if _k == k:
#                     selected_key["value"] = k
#                     display.value = _t
#                     display.update()
#                     return True
#             return False

#         @staticmethod
#         def clear():
#             selected_key["value"] = None
#             display.value = None
#             display.update()

#         @staticmethod
#         def control():
#             return main

#     return main, API


# def create_searchable_dropdown(
#         page: ft.Page, 
#         label: str, 
#         options: list, 
#         on_change=None, 
#         width: int | None = 300
#     ):

#     selected_key = {"value": None}
#     expanded = {"value": False}

#     # MAIN DISPLAY FIELD
#     display = ft.TextField(
#         label=label,
#         read_only=True,
#         width=width,
#         suffix_icon=ft.Icons.ARROW_DROP_DOWN,
#         on_click=lambda e: toggle_dropdown(e),
#     )

#     # SEARCH FIELD INSIDE DROPDOWN
#     search_input = ft.TextField(
#         hint_text="Search...",
#         visible=False,
#         on_change=lambda e: filter_list(e),
#     )

#     # LISTVIEW wrapped inside scroll-isolated container
# #     listview = ft.ListView(expand=True, spacing=4, height=200)

#     inner_list = ft.ListView(
#         expand=True,
#         spacing=4,
#         auto_scroll=False
#     )

#     list_container = ft.Container(
#         height=200,
#         clip_behavior=ft.ClipBehavior.HARD_EDGE,  # ★ prevents parent scroll
#         content=inner_list
#     )

#     # DROPDOWN PANEL
#     dropdown_panel = ft.Container(
#         content=ft.Column([search_input, list_container], spacing=6),
#         visible=False,
#         width=width,
#         padding=8,
#         bgcolor=ft.Colors.SURFACE,
#         border_radius=8,
#         border=ft.border.all(1, ft.Colors.GREY_300),
#         clip_behavior=ft.ClipBehavior.HARD_EDGE,  # ★ isolates scroll
#     )

#     main = ft.Column([display, dropdown_panel], spacing=4)

#     # BUILD OPTION LIST
#     def build_list(items):
#         inner_list.controls.clear()
#         for key, text in items:
#             inner_list.controls.append(
#                 ft.Container(
#                     content=ft.Text(text),
#                     padding=8,
#                     border_radius=6,
#                     ink=True,
#                     on_click=lambda e, k=key, t=text: select_item(k, t),
#                 )
#             )

#     build_list(options)

#     # EVENTS
#     def toggle_dropdown(e):
#         expanded["value"] = not expanded["value"]
#         dropdown_panel.visible = expanded["value"]
#         search_input.visible = expanded["value"]

#         if expanded["value"]:
#             search_input.value = ""
#             filter_list(None)

#         dropdown_panel.update()
#         display.update()
#         search_input.update()
#         inner_list.update()

#     def filter_list(e):
#         q = (search_input.value or "").lower()
#         filtered = [(k, t) for (k, t) in options if q in t.lower()]
#         build_list(filtered)
#         inner_list.update()

#     def select_item(key, text):
#         selected_key["value"] = key
#         display.value = text

#         expanded["value"] = False
#         dropdown_panel.visible = False
#         search_input.visible = False

#         display.update()
#         dropdown_panel.update()
#         inner_list.update()
#         search_input.update()

#         if on_change:
#             on_change(key)

#     # RETURN API CLASS
#     class API:
#         def get(self):
#             return selected_key["value"]

#         def get_text(self):
#             return display.value

#         def set(self, k):
#             # find text for key
#             for _k, _t in options:
#                 if _k == k:
#                     selected_key["value"] = k
#                     display.value = _t
#                     display.update()
#                     return True
#             return False

#         def clear(self):
#             selected_key["value"] = None
#             display.value = None
#             display.update()

#         def set_options(self, new_options):
#             nonlocal options  # <--- REQUIRED so API can modify outer variable
#             options = new_options
#             build_list(options)
#             inner_list.update()

#         def refresh(self):
#             display.update()
#             dropdown_panel.update()
#             inner_list.update()
#             search_input.update()

#         def control(self):
#             return main


#     return main, API()


def create_searchable_dropdown(
        page: ft.Page, 
        label: str, 
        options: list, 
        on_change=None, 
        width: int | None = 300
    ):

    selected_key = {"value": None}
    expanded = {"value": False}

    # MAIN DISPLAY FIELD
    display = ft.TextField(
        label=label,
        read_only=True,
        width=width,
        suffix_icon=ft.Icons.ARROW_DROP_DOWN,
        on_click=lambda e: toggle_dropdown(),
    )

    # SEARCH FIELD
    def on_search():
        if is_mounted["value"]:
            filter_list()

    search_input = ft.TextField(
        hint_text="Search...",
        visible=False,
        on_change=lambda e: filter_list() if dropdown_panel.visible and is_mounted["value"] else None,
    )

    # LISTVIEW (inside scroll-isolated container)
    inner_list = ft.ListView(
        expand=True,
        spacing=4,
        auto_scroll=False
    )

    list_container = ft.Container(
        height=200,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=inner_list
    )

    # DROPDOWN PANEL
    dropdown_panel = ft.Container(
        content=ft.Column([search_input, list_container], spacing=6),
        visible=False,
        width=width,
        padding=8,
        bgcolor=ft.Colors.SURFACE,
        border_radius=8,
        border=ft.border.all(1, ft.Colors.GREY_300),
        clip_behavior=ft.ClipBehavior.HARD_EDGE
    )

    main = ft.Column([display, dropdown_panel], spacing=4)
    
    wrapper = ft.Container(content=main)

    
    is_mounted = {"value": False}

    def on_mount():
        is_mounted["value"] = True

    # main.did_mount = on_mount
    # wrapper.did_mount = on_mount
    wrapper.did_mount = on_mount

    # BUILD OPTION LIST
    def build_list(items):
        inner_list.controls.clear()
        for key, text in items:
            inner_list.controls.append(
                ft.Container(
                    content=ft.Text(text),
                    padding=8,
                    border_radius=6,
                    ink=True,
                    on_click=lambda e, k=key, t=text: select_item(k, t),
                )
            )

    build_list(options)

    # EVENTS — NO CHILD UPDATES!
    def toggle_dropdown():
        if not is_mounted["value"]:
            return
        expanded["value"] = not expanded["value"]

        dropdown_panel.visible = expanded["value"]
        search_input.visible = expanded["value"]

        if expanded["value"]:
            search_input.value = ""
            # Only filter AFTER control is mounted
            # if is_mounted["value"]:
            #     filter_list()
            # filter_list()
            build_list(options)
            # if is_mounted["value"]:
            #     inner_list.update()
            if inner_list.page:
                inner_list.update()

        # main.update()       # SAFE
        # if is_mounted["value"] and main.page is not None:
        if main.page is not None:
            display.update()
            dropdown_panel.update()
            search_input.update()
            inner_list.update()

    def filter_list():
        if not is_mounted["value"]:
            return
        if not dropdown_panel.visible:
            return
        q = (search_input.value or "").lower()
        filtered = [(k, t) for (k, t) in options if q in t.lower()]
        build_list(filtered)
        # main.update()       # SAFE
        # if inner_list.page is not None:
        #     inner_list.update()
        if inner_list.page:
            inner_list.update()
        # inner_list.update()

    def select_item(key, text):
        selected_key["value"] = key
        display.value = text

        expanded["value"] = False
        dropdown_panel.visible = False
        search_input.visible = False

        if on_change:
            on_change(key)

        # main.update()       # SAFE
        page.update()

    wrapper = ft.Container(content=main)

    
    is_mounted = {"value": False}

    def on_mount():
        is_mounted["value"] = True

    # main.did_mount = on_mount
    # wrapper.did_mount = on_mount
    wrapper.did_mount = on_mount


    # RETURN API CLASS
    class API:
        def get(self):
            return selected_key["value"]

        def get_text(self):
            return display.value

        def set(self, k):
            for _k, _t in options:
                if _k == k:
                    selected_key["value"] = k
                    display.value = _t
                    # main.update()
                    page.update()
                    return True
            return False

        def clear(self):
            selected_key["value"] = None
            display.value = ""

            search_input.value = ""

            # rebuild from full list
            build_list(options)

            if main.page is not None:
                display.update()
                inner_list.update()

        def set_options(self, new_options):
            nonlocal options
            options = new_options
            build_list(options)
            # main.update()
            page.update()
            # If dropdown is open, re-filter
            if expanded["value"] and is_mounted["value"]:
                filter_list()

            # Always update inner content
            if main.page is not None:
                inner_list.update()

        def refresh(self):
            # main.update()
            page.update()

        def control(self):
            return wrapper

    return wrapper, API()

