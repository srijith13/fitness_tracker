# ui.py (UPDATED)
import flet as ft
import datetime
from typing import Tuple

# --- Import your existing data/utility functions ---
from utils import iso_today
from models import (
    add_weight_entry,
    list_weights,
    add_exercise,
    list_exercises,
    detect_prs,
)
from charts import generate_weight_chart
from prs import get_muscle_groups,get_prs_for_muscle_group,create_searchable_dropdown,get_exercises_for_mg
from csv_io import export_all, import_weights, import_exercises

# ---- Styling constants ----
PRIMARY_COLOR = ft.Colors.BLUE_600
ACCENT_COLOR = ft.Colors.RED_600
CARD_RADIUS = 14
MOBILE_BREAKPOINT = 720  # px


# ---- small helpers ----
def card(content, width=None, padding=14, bgcolor=None):
    return ft.Container(
        content=content,
        padding=padding,
        width=width,
        bgcolor=bgcolor or ft.Colors.SURFACE,
        border_radius=ft.border_radius.all(CARD_RADIUS),
        shadow=ft.BoxShadow(
            blur_radius=12,
            spread_radius=1,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
    )


def stat_block(title: str, value: str, subtitle: str = "", color=None):
    return ft.Column(
        [
            ft.Text(title, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=color or ft.Colors.ON_SURFACE),
            ft.Text(subtitle, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
        ],
        tight=True,
    )


# ---- UI building function (entrypoint) ----
def build_app(page: ft.Page):
    page.title = "Fitness Tracker — Responsive"
    page.padding = 12
    page.spacing = 12
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- Reactive state ---
    is_mobile = page.width < MOBILE_BREAKPOINT

    # Responsive toggle
    def on_resize(e):
        nonlocal is_mobile
        is_mobile = page.width < MOBILE_BREAKPOINT
        rebuild_layout()

    page.on_resize = on_resize

    # ----------------------------
    # Top bar: title, profile, theme toggle
    # ----------------------------
    title_label = ft.Text("Fitness Tracker", size=20, weight=ft.FontWeight.BOLD)
    profile_avatar = ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON), radius=20)
    theme_btn = ft.IconButton(icon=ft.Icons.BRIGHTNESS_6, on_click=lambda e: toggle_theme(e))


    # ----------------------------
    # Global date picker + label + clear
    # ----------------------------
    # date_picker = ft.DatePicker(value=datetime.date.today())
    # page.overlay.append(date_picker)

    # date_label = ft.Text(date_picker.value.isoformat(), size=12)

    # def on_date_change(e):
    #     date_label.value = date_picker.value.isoformat()
    #     page.update()

    # date_picker.on_change = on_date_change

    # def clear_date(e):
    #     date_picker.value = datetime.date.today()
    #     date_label.value = date_picker.value.isoformat()
    #     page.update()

    # date_clear_btn = ft.TextButton("Clear", on_click=clear_date)

#New
    date_label = ft.Text("No date selected", size=13, italic=True)

    date_picker = ft.DatePicker(
        first_date=datetime.datetime(2000, 10, 1),
        on_change=lambda e: (
            date_label.__setattr__("value", date_picker.value.isoformat()),
            page.update()
        )
    )

    page.overlay.append(date_picker)

    def clear_date(e):
        date_picker.value = None
        date_label.value = "No date selected"
        page.update()

    # ----------------------------
    # INPUT FIELDS
    # ----------------------------
    weight_tf = ft.TextField(label="Weight (kg)")
    weight_notes = ft.TextField(label="Notes", multiline=True)
    
    # SAVE WEIGHT ENTRY
    def save_weight(e):
        sel_date = date_picker.value or datetime.date.today()
        val = validate_float(weight_tf.value)

        if val is None:
            page.snack_bar = ft.SnackBar(ft.Text("Enter valid weight"))
            page.snack_bar.open = True
            page.update()
            return

        add_weight_entry(sel_date.isoformat(), val, weight_notes.value)
        weight_tf.value = ""
        weight_notes.value = ""
        refresh_all()

    save_weight_btn = ft.ElevatedButton( text="Save weight",on_click=save_weight)
    
    # muscle_group = ft.Dropdown(label="Muscle Group",options=[ft.dropdown.Option(key=str(m["id"]), text=m["muscle_group"].capitalize()) for m in get_muscle_groups()],)
    muscle_options = [(str(m["id"]), m["muscle_group"].title()) for m in get_muscle_groups()]

    def on_muscle_selected(mg_id):
        exercises = get_exercises_for_mg(mg_id)   # <- YOU MUST PROVIDE THIS FUNCTION!

        # Convert to the dropdown option format
        ex_options = [(str(e["id"]), e["exercise"].title()) for e in exercises]

        # Update exercise dropdown
        exercise_dropdown_api.set_options(ex_options)
        exercise_dropdown_api.clear()      # reset previous selection
        exercise_dropdown_api.refresh()    # update UI

    dropdown_control, dropdown_api = create_searchable_dropdown(
        page,
        "Muscle Group",
        muscle_options,
        # on_change=lambda key: print("selected id:", key),
        on_change=on_muscle_selected,
        width=300,
    )
    page.add(dropdown_control) 
    # ex_name = ft.TextField(label="Exercise")
    exercise_dropdown_control, exercise_dropdown_api = create_searchable_dropdown(
        page,
        "Exercise",
        [],
        width=300,
    )
    page.add(exercise_dropdown_control)
    sets_completed_tf = ft.TextField(label="Sets completed", width=140)
    ex_notes = ft.TextField(label="Notes", multiline=True)
    sets_container = ft.Column(spacing=8)
    
    # add_set_btn = ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, icon_color=ft.Colors.GREEN) 

    
    def add_set_row(e=None):
        reps = ft.TextField(label="Reps", width=80)
        wt = ft.TextField(label="Weight", width=100)
        del_btn = ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED)
        row = ft.Row([reps, wt, del_btn], spacing=8)

        def on_del(ev):
            sets_container.controls.remove(row)
            page.update()

        del_btn.on_click = on_del
        sets_container.controls.append(row)
        page.update()

    # add_set_btn.on_click = add_set_row
    add_set_btn = ft.ElevatedButton(
        icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
        icon_color=ft.Colors.GREEN,
        text="Add Reps",
        on_click=add_set_row,
    )

    def get_selected_option_name(dropdown):
        for opt in dropdown.options:
            if opt.key == dropdown.value:
                return opt.text
        return None

    # SAVE EXERCISE ENTRY
    def save_exercise(e):
        sel_date = date_picker.value or datetime.date.today()
        
        
        # Get selected muscle group ID and name
        # muscle_group_id = muscle_group.value
        # muscle_group_name = get_selected_option_name(muscle_group)
        mg_id = dropdown_api.get()
        if not mg_id:
            page.snack_bar = ft.SnackBar(ft.Text("Select a muscle group"))
            page.snack_bar.open = True
            page.update()
            return

        # if not muscle_group_id:
        #     page.snack_bar = ft.SnackBar(ft.Text("Select a muscle group"))
        #     page.snack_bar.open = True
        #     return

        # if not ex_name.value.strip():
        #     page.snack_bar = ft.SnackBar(ft.Text("Exercise name required"))
        #     page.snack_bar.open = True
        #     return
        ex_id = exercise_dropdown_api.get()
        if not ex_id:
            page.snack_bar = ft.SnackBar(ft.Text("Select an exercise"))
            page.snack_bar.open = True
            page.update()
            return
        ex_name = exercise_dropdown_api.get_text()

        sets = []
        for r in sets_container.controls:
            reps = int(r.controls[0].value or 0)
            wt = float(r.controls[1].value or 0)
            sets.append({"reps": reps, "weight": wt})

        add_exercise(sel_date.isoformat(), ex_name, int(sets_completed_tf.value or 0), sets, ex_notes.value, mg_id) #muscle_group_id ex_name.value
        # muscle_group.value = None
        dropdown_api.clear()
        # ex_name.value = ""
        exercise_dropdown_api.clear()
        sets_completed_tf.value = ""
        sets_container.controls.clear()
        ex_notes.value = ""
        refresh_all()

    save_exercise_btn =  ft.ElevatedButton("Save Exercise", on_click=save_exercise)

    # ----------------------------
    # Timeline (Scrollable History)
    # ----------------------------
    timeline_column = ft.Column(expand=True,scroll=ft.ScrollMode.AUTO)      # ✔ SCROLLABLE HISTORY)
    stats_column = ft.Column(expand=True,scroll=ft.ScrollMode.AUTO)
    # ----------------------------
    # Chart area (weight graph)
    # ----------------------------
    # weight_line_chart = ft.LineChart(
    #     data_series=[],
    #     width=600,
    #     height=280,
    #     animate=300,
    #     min_y=0,
    #     expand=True,
    # )
     # Create the chart control
    weight_chart = ft.LineChart(
        data_series=[],
        width=600,
        height=300,
        border=ft.border.all(3, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=1, color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
        ),
        vertical_grid_lines=ft.ChartGridLines(
            interval=1, color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
        ),
        left_axis=ft.ChartAxis(),
        bottom_axis=ft.ChartAxis(),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
        min_y=0,
        animate=300,
        expand=True,
    )
    

    # ----------------------------
    # File picker for CSV import
    # ----------------------------
    file_picker = ft.FilePicker(on_result=lambda e: on_file_chosen(e))
    page.overlay.append(file_picker)

    # ----------------------------
    # ACTION HANDLERS
    # ----------------------------
    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        )
        page.update()

    def validate_float(s):
        try:
            return float(s)
        except:
            return None

    
    # ----------------------------
    # LIVE STATS FROM DB
    # ----------------------------
    def compute_stats():
        weights = list_weights()
        # exercises = list_exercises()
        if not weights:
            return None, None, None, None

        normalized = []
        for item in weights:
            d = item["date"]
            if isinstance(d, str):
                try:
                    # Try parsing date only
                    d_obj = datetime.date.fromisoformat(d)
                except ValueError:
                    # Parse full datetime, extract date
                    try:
                        d_obj = datetime.datetime.fromisoformat(d).date()
                    except Exception:
                        continue  # skip invalid entries
            else:
                d_obj = d

            normalized.append({"date": d_obj, "weight_kg": item["weight_kg"]})

        # If ALL items were invalid → still return safe defaults
        if not normalized:
            return None, None, None, None

        # Sort by date
        normalized.sort(key=lambda x: x["date"])

        # Last weight
        last_weight = normalized[-1]["weight_kg"]

        # 7-day average
        cutoff = datetime.date.today() - datetime.timedelta(days=7)
        last7 = [x["weight_kg"] for x in normalized if x["date"] >= cutoff]
        avg7 = sum(last7) / len(last7) if last7 else None

        # NEW: all-time min & max
        all_weights = [x["weight_kg"] for x in normalized]
        min_weight = min(all_weights)
        max_weight = max(all_weights)

        return last_weight, avg7, max_weight, min_weight
    # ----------------------------
    # Quick stats - dynamic values
    # ----------------------------
    last_weight_label = ft.Text("-", size=18, weight=ft.FontWeight.BOLD)
    avg7_label = ft.Text("-", size=14)
    max_weights_label = ft.Text("-", size=14)
    min_weights_label = ft.Text("-", size=14)

    # lw, a7, max_w, min_w= compute_stats()

    # last_weight_label.value = f"{lw} kg" if lw else "-"
    # avg7_label.value = f"{a7:.2f} kg" if a7 else "-"
    # max_weights_label.value = f"{max_w:.2f} kg" if max_w else "-"
    # min_weights_label.value = f"{min_w:.2f} kg" if min_w else "-"


    # ----------------------------
    # Update weight graph
    # ----------------------------
    def refresh_chart():
        # points, labels = generate_weight_chart()

        # if not points:
        #     weight_line_chart.data_series = []
        #     return

        # data_points = [ft.LineChartDataPoint(x=p[0], y=p[1]) for p in points]

        # weight_line_chart.data_series = [
        #     ft.LineChartData(
        #         data_points=data_points,
        #         stroke_width=3,
        #         color=PRIMARY_COLOR,
        #     )
        # ]

        # weight_line_chart.bottom_axis = ft.ChartAxis(
        #     labels=[
        #         ft.ChartAxisLabel(value=i, label=ft.Text(labels[i], size=10))
        #         for i in range(len(labels))
        #     ],
        #     labels_interval=1,
        # )
        points, labels = generate_weight_chart()
        weight_chart.data_series = [
            ft.LineChartData(
                data_points=[
                    ft.LineChartDataPoint(x, y)
                    for x, y in points
                ],
                stroke_width=4,
            )
        ]

        # Extract only Y-values for left-axis labels
        ys = [y for _, y in points]

        # Build Y-axis labels (weights)
        weight_chart.left_axis = ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(
                    value=y,
                    label=ft.Text(str(y), size=12)
                )
                for y in sorted(set(ys))
            ],
            labels_interval=0.5,
            labels_size=40,
        )

        # Build X-axis labels (dates)
        weight_chart.bottom_axis = ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(labels[i], size=12)
                )
                for i in range(len(labels))
            ],
            labels_interval=0.5,
            labels_size=32,
        )
        weight_chart.min_y = min(ys)-0.5

        page.update()


    # ----------------------------
    # PR 
    # ----------------------------
    def pr_group_row(id,muscle_group,mg_image):
        return ft.Container(
            content=ft.Row(
                [   
                    ft.Text(muscle_group, size=16, weight=ft.FontWeight.W_500),
                    ft.Image(src_base64=mg_image,width=35,height=35),
                    ft.Icon(name=ft.Icons.ARROW_FORWARD_IOS, size=16),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=12,
            border_radius=10,
            bgcolor=ft.Colors.BLUE,
            on_click=lambda e, m=muscle_group: open_pr_detail_page(id,m),
        )
    
    def build_pr_card():
        # muscle_groups = get_muscle_groups()
        return card(
            ft.Column(
                [
                    ft.Text("Personal Records", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    *[pr_group_row(m["id"],m["muscle_group"].title(), m["mg_image"]) for m in get_muscle_groups()]
                ],
                spacing=8
            )
        )

    def open_pr_detail_page(id,muscle_group):
        prs = get_prs_for_muscle_group(id,muscle_group)
        # prs → { "Bench Press": {"weight": 100, "date": datetime}, ... }

        # Sort PRs by heaviest → lightest
        sorted_prs = sorted(
            prs.items(),
            key=lambda x: x[1]["weight"],
            reverse=True
        )

        rows = []
        for ex_name, data in sorted_prs:
            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(ex_name, size=16),
                            ft.Text(f"{data['weight']} kg", weight=ft.FontWeight.BOLD),
                            ft.Text(data['date'].strftime("%Y-%m-%d"), size=12),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    bgcolor=ft.Colors.BLUE, #ft.Colors.ON_SURFACE_VARIANT,
                    border_radius=8,
                    margin=ft.margin.only(bottom=6),
                )
            )

        # PUSH NEW VIEW
        page.views.append(
            ft.View(
                route=f"/pr/{muscle_group}",
                controls=[
                    ft.AppBar(
                        title=ft.Text(f"{muscle_group} — PRs"),
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: go_back(),
                        ),
                    ),
                    ft.Column(rows, scroll=ft.ScrollMode.AUTO),
                ],
            )
        )

        page.update()


    def go_back():
        page.views.pop()
        page.update()


    # ----------------------------
    # TIMELINE (HISTORY) REFRESH
    # ----------------------------
    def refresh_timeline():
        timeline_column.controls.clear()
        stats_column.controls.clear()


        w = list_weights()
        ex = list_exercises()
        prs = detect_prs()

        combined = []
        for r in w:
            combined.append((r["date"], "weight", r))
        for r in ex:
            combined.append((r["date"], "exercise", r))

        # Normalize dates
        def norm(d):
            # return datetime.date.fromisoformat(d) if isinstance(d, str) else d
            if isinstance(d, str):
                try:
                    # Try date only (YYYY-MM-DD)
                    return datetime.date.fromisoformat(d)
                except ValueError:
                    # Try full datetime (YYYY-MM-DDTHH:MM:SS)
                    return datetime.datetime.fromisoformat(d).date()
            return d

        combined.sort(key=lambda x: norm(x[0]))

        for d, typ, payload in combined[::-1]:  # newest first
            d = norm(d)

            if typ == "weight":
                entry = card(
                    ft.Column(
                        [
                            ft.Text(f"{payload['weight_kg']} kg", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(str(d), size=10),
                            ft.Text(payload.get("notes") or "", size=12, style=ft.TextStyle(italic=True)),
                        ]
                    ),
                    width=320,
                )
            else:
                sets_txt = "\n".join(
                    [f"{i+1}. {s['reps']} reps @ {s['weight']}kg" for i, s in enumerate(payload["sets"])]
                )

                max_w = max([s["weight"] for s in payload["sets"]]) if payload["sets"] else 0
                pr_flag = " 🏆" if payload["name"].lower() in prs and prs[payload["name"].lower()] == max_w else ""

                entry = card(
                    ft.Column(
                        [
                            ft.Text(f"{payload['name']}{pr_flag}", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                spans=[
                                    ft.TextSpan(
                                        f"Reps: {payload['sets_completed']} ",
                                        style=ft.TextStyle(size=14, italic=True),
                                    ),
                                    ft.TextSpan(
                                        str(d),
                                        style=ft.TextStyle(size=10),
                                    ),
                                ]
                            ),
                            ft.Text(sets_txt, size=12),
                        ]
                    ),
                    width=320,
                )

            timeline_column.controls.append(entry)

        lw, a7, max_w, min_w= compute_stats()

        last_weight_label.value = f"{lw} kg" if lw else "-"
        avg7_label.value = f"{a7:.2f} kg" if a7 else "-"
        max_weights_label.value = f"{max_w:.2f} kg" if max_w else "-"
        min_weights_label.value = f"{min_w:.2f} kg" if min_w else "-"
        stats_entry1 = card(
                    ft.Column(
                        [
                            ft.Text("Quick Stats", weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    stat_block("Last weight", last_weight_label.value),
                                    stat_block("7d avg weight", avg7_label.value),
                                    stat_block("Max Weight", max_weights_label.value),
                                    stat_block("Min Weight", min_weights_label.value),
                                ],
                                spacing=12,
                            ),
                        ]
                    )
                )
        stats_entry2 = card(
                    ft.Column(
                        [
                            ft.Text("Log Weight", weight=ft.FontWeight.BOLD),
                            weight_tf,
                            weight_notes,
                            # ft.ElevatedButton("Save weight", on_click=save_weight),
                            save_weight_btn,
                        ]
                    )
                )
        stats_entry3 = card(
                    ft.Column(
                        [
                            ft.Text("Log Exercise", weight=ft.FontWeight.BOLD),
                            # muscle_group,
                            # dropdown_control,
                            dropdown_api.control(),
                            # ex_name,
                            exercise_dropdown_api.control(),
                            sets_completed_tf,
                            # ft.TextButton("Add Set", on_click=add_set_row),
                            # ft.Row([add_set_btn,ft.Text("Add Reps")]),
                            add_set_btn,
                            sets_container,
                            ex_notes,
                            # ft.ElevatedButton("Save Exercise", on_click=save_exercise),
                            save_exercise_btn,
                        ]
                    )
                )
            
        stats_column.controls.append(stats_entry1)
        stats_column.controls.append(stats_entry2)
        stats_column.controls.append(stats_entry3)


        page.update()
        

    # ----------------------------
    # Refresh ALL UI components
    # ----------------------------
    def refresh_all():
        refresh_chart()
        refresh_timeline()

        # lw, a7, max_w, min_w = compute_stats()

        # last_weight_label.value = f"{lw} kg" if lw else "-"
        # avg7_label.value = f"{a7:.2f} kg" if a7 else "-"
        # max_weights_label.value = f"{max_w:.2f} kg" if max_w else "-"
        # min_weights_label.value = f"{min_w:.2f} kg" if min_w else "-"

        page.update()

    # ----------------------------
    # Responsive Layout
    # ----------------------------
    def rebuild_layout():
        page.controls.clear()
        # stats_column.controls.clear()
         # top bar row

        # top bar
        top_row = ft.Row(
            [
                title_label,
                ft.Container(expand=True),
                date_label,
                ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=lambda e: (setattr(date_picker, "open", True), page.update())),
                ft.IconButton(icon=ft.Icons.CALENDAR_TODAY,tooltip="Clear Date",on_click=clear_date), 
                theme_btn,
                profile_avatar,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


        # LEFT PANEL stats_column
        # left_panel = ft.Column(
        #     [
        #         ft.Text("Stats", size=18, weight=ft.FontWeight.BOLD),
        #         card(
        #             ft.Column(
        #                 [
        #                     ft.Text("Quick Stats", weight=ft.FontWeight.BOLD),
        #                     ft.Row(
        #                         [
        #                             stat_block("Last weight", last_weight_label.value),
        #                             stat_block("7d avg weight", avg7_label.value),
        #                             stat_block("Max Weight", max_weights_label.value),
        #                             stat_block("Min Weight", min_weights_label.value),
        #                         ],
        #                         spacing=12,
        #                     ),
        #                 ]
        #             )
        #         ),
        #         card(
        #             ft.Column(
        #                 [
        #                     ft.Text("Log Weight", weight=ft.FontWeight.BOLD),
        #                     weight_tf,
        #                     weight_notes,
        #                     # ft.ElevatedButton("Save weight", on_click=save_weight),
        #                     save_weight_btn,
        #                 ]
        #             )
        #         ),
        #         card(
        #             ft.Column(
        #                 [
        #                     ft.Text("Log Exercise", weight=ft.FontWeight.BOLD),
        #                     ex_name,
        #                     sets_completed_tf,
        #                     # ft.TextButton("Add Set", on_click=add_set_row),
        #                     # ft.Row([add_set_btn,ft.Text("Add Reps")]),
        #                     add_set_btn,
        #                     sets_container,
        #                     ex_notes,
        #                     # ft.ElevatedButton("Save Exercise", on_click=save_exercise),
        #                     save_exercise_btn,
        #                 ]
        #             )
        #         ),
        #     ],
        #     # spacing=12,
            
        #     # scroll=ft.ScrollMode.AUTO,
        #     # expand=True,
        #     # alignment=ft.MainAxisAlignment.START
        # )
        # RIGHT PANEL
        left_panel = ft.Column(
            [
                ft.Text("Stats", size=18, weight=ft.FontWeight.BOLD),
                card(stats_column),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )

        # CENTER PANEL
        center_panel = ft.Column(
            [
                ft.Text("Weight Progress", size=18, weight=ft.FontWeight.BOLD),
                card(
                    weight_chart,
                ),
                build_pr_card(),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # RIGHT PANEL
        right_panel = ft.Column(
            [
                ft.Text("History", size=18, weight=ft.FontWeight.BOLD),
                card(timeline_column),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
        
        if page.width < MOBILE_BREAKPOINT:
            # Mobile layout: stack vertically
            col = ft.Column(
                [
                    top_row,
                    card(ft.Column([stat_block("Last weight", last_weight_label.value, ""), stat_block("7-day avg", avg7_label.value, "")]), padding=12),
                    card(ft.Column([ft.Text("Progress", weight=ft.FontWeight.BOLD), weight_chart]), padding=12),
                    card(ft.Column([ft.Text("Log Weight", weight=ft.FontWeight.BOLD), weight_tf, weight_notes, save_weight_btn]), padding=12),
                    card(ft.Column([ft.Text("Log Exercise", weight=ft.FontWeight.BOLD), dropdown_api.control(),exercise_dropdown_api.control(), sets_completed_tf, add_set_btn, sets_container, ex_notes,save_exercise_btn,]), padding=12), #muscle_group, dropdown_control ex_name,
                    # ft.Text("History", size=16, weight=ft.FontWeight.BOLD),
                    card(timeline_column, padding=12),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            )
            page.add(col)
        else:
            # Desktop/tablet: 3-column layout
            left_col = ft.Container(left_panel, width=430)
            center_col = ft.Container(center_panel, width=625,  expand=True, padding=6)
            right_col = ft.Container(right_panel, width=400, padding=6)

            main_row = ft.Row([left_col, center_col, right_col], expand=True, spacing=12) # , right_col
            page.add(top_row, ft.Divider(height=8), main_row)

 
        

        # if is_mobile:
        #     # Mobile stacks vertically
        #     page.add(top_row, left_panel, center_panel, right_panel)
        # else:
        #     # Desktop → 3-column layout
        #     page.add(
        #         top_row,
        #         ft.Row(
        #             [
        #                 ft.Container(left_panel, width=340),
        #                 ft.Container(center_panel, expand=True),
        #                 ft.Container(right_panel, width=380),
        #             ],
        #             spacing=12,
        #             expand=True,
        #         ),
        #     )

        refresh_all()
        # ensure chart and timeline are populated
        # refresh_all()
        page.update()

    # initial layout build
    rebuild_layout()
