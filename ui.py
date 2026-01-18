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
    list_weights_date,
    list_cardio_date,
    list_exercises_date,
    list_muscle_group_date,
    list_mg_exercises_date,
)
from charts import generate_weight_chart
from prs import get_muscle_groups,get_prs_for_muscle_group,create_searchable_dropdown,get_exercises_for_mg
from csv_io import export_all, import_weights, import_exercises
import calendar

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
        raw_s = sel_date
        if isinstance(raw_s, datetime.datetime):
            s = raw_s.date()
        elif isinstance(raw_s, datetime.date):
            s = raw_s
        else:
            s = datetime.date.fromisoformat(raw_s)

        val = validate_float(weight_tf.value)

        if val is None:
            page.snack_bar = ft.SnackBar(ft.Text("Enter valid weight"))
            page.snack_bar.open = True
            page.update()
            return

        add_weight_entry(s, val, weight_notes.value)
        weight_tf.value = ""
        weight_notes.value = ""
                # --- FIX DROPDOWNS ---
        # Reload muscle group dropdown
        dropdown_api.set_options(muscle_options)
        dropdown_api.clear()

        # Clear and reload exercise dropdown
        exercise_dropdown_api.set_options([])
        exercise_dropdown_api.clear()

        dropdown_api.refresh()
        exercise_dropdown_api.refresh()
        refresh_all()

        page.update()

    save_weight_btn = ft.ElevatedButton( text="Save weight",on_click=save_weight)
    
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
        on_change=on_muscle_selected,
        width=300,
    )
    page.add(dropdown_control) 
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

    def save_exercise(e):
        sel_date = date_picker.value or datetime.date.today()
        
        raw_s = sel_date
        if isinstance(raw_s, datetime.datetime):
            s = raw_s.date()
        elif isinstance(raw_s, datetime.date):
            s = raw_s
        else:
            s = datetime.date.fromisoformat(raw_s)

        mg_id = dropdown_api.get()
        if not mg_id:
            page.snack_bar = ft.SnackBar(ft.Text("Select a muscle group"))
            page.snack_bar.open = True
            page.update()
            return
        
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

        add_exercise(s, ex_name, int(sets_completed_tf.value or 0), sets, ex_notes.value,ex_id, mg_id)

        # CLEAR UI FIELDS
        sets_container.controls.clear()
        sets_completed_tf.value = ""
        ex_notes.value = ""

        # --- FIX DROPDOWNS ---
        # Reload muscle group dropdown
        dropdown_api.set_options(muscle_options)
        dropdown_api.clear()

        # Clear and reload exercise dropdown
        exercise_dropdown_api.set_options([])
        exercise_dropdown_api.clear()

        dropdown_api.refresh()
        exercise_dropdown_api.refresh()
        
        page.update()
        refresh_all()

    save_exercise_btn =  ft.ElevatedButton("Save Exercise", on_click=save_exercise)


    # ----------------------------
    # Time picker (must be overlay)
    # ----------------------------
    cardio_type_dd = ft.Dropdown(
        label="Cardio Type",
        width=300,
        options=[
            ft.dropdown.Option("Walk"),
            ft.dropdown.Option("Brisk Walk"),
            ft.dropdown.Option("Jog"),
            ft.dropdown.Option("Run"),
            ft.dropdown.Option("Other"),
        ],
    )
    cardio_notes = ft.TextField(label="Notes", multiline=True)
    cardio_time_picker = ft.TimePicker(value=datetime.time(0, 0), time_picker_entry_mode=ft.TimePickerEntryMode.INPUT,)
    page.overlay.append(cardio_time_picker)

    # ----------------------------
    # Display field
    # ----------------------------
    cardio_time_display = ft.TextField(
        label="Duration (HH:MM)",
        read_only=True,
        width=180,
        value="00:00"
    )

    # ----------------------------
    # Handle picker change
    # ----------------------------
    def on_time_change(e):
        if cardio_time_picker.value:
            h = cardio_time_picker.value.hour
            m = cardio_time_picker.value.minute
            cardio_time_display.value = f"{h:02d}:{m:02d}"
            page.update()

    cardio_time_picker.on_change = on_time_change

    # ----------------------------
    # Open picker explicitly
    # ----------------------------
    def open_time_picker(e):
        cardio_time_picker.open = True
        page.update()

     # ----------------------------
    # Clear Button
    # ----------------------------
    def clear_time(e):
        cardio_time_picker.value = datetime.time(0, 0)
        cardio_time_display.value = "00:00"
        page.update()

    # SAVE cardio ENTRY
    def save_cardio(e):
        sel_date = date_picker.value or datetime.date.today()

        if isinstance(sel_date, datetime.datetime):
            s = sel_date.date()
        elif isinstance(sel_date, datetime.date):
            s = sel_date
        else:
            s = datetime.date.fromisoformat(sel_date)
        # print("date s",s.type())
        if not cardio_type_dd.value:
            page.snack_bar = ft.SnackBar(ft.Text("Select cardio type"))
            page.snack_bar.open = True
            page.update()
            return

        if not cardio_time_picker.value:
            page.snack_bar = ft.SnackBar(ft.Text("Select cardio duration"))
            page.snack_bar.open = True
            page.update()
            return

        # Convert to string
        duration = cardio_time_picker.value.strftime("%H:%M:%S")
        add_cardio_entry(s,cardio_type_dd.value,cardio_notes.value,duration)

        # ---- CLEAR ----
        cardio_type_dd.value = None
        cardio_time_picker.value = datetime.time(0, 0)
        cardio_time_display.value = "00:00"
        cardio_notes.value = ""
        
        # --- FIX DROPDOWNS ---
        # Reload muscle group dropdown
        dropdown_api.set_options(muscle_options)
        dropdown_api.clear()

        # Clear and reload exercise dropdown
        exercise_dropdown_api.set_options([])
        exercise_dropdown_api.clear()

        dropdown_api.refresh()
        exercise_dropdown_api.refresh()
        refresh_all()

        page.update()

    save_cardio_btn = ft.ElevatedButton( text="Save cardio",on_click=save_cardio)

    time_row = ft.Row(
        [
            cardio_time_display,

            ft.IconButton(
                icon=ft.Icons.ACCESS_TIME,
                tooltip="Pick duration",
                on_click=open_time_picker,
            ),

            ft.IconButton(
                icon=ft.Icons.CLEAR,
                tooltip="Clear duration",
                on_click=clear_time,
            ),
        ],
        spacing=6,
        )


    # ----------------------------
    # Timeline (Scrollable History)
    # ----------------------------
    timeline_column = ft.Column(expand=True,scroll=ft.ScrollMode.AUTO)      # ✔ SCROLLABLE HISTORY)
    stats_column = ft.Column(expand=True,scroll=ft.ScrollMode.AUTO)

    # ----------------------------
    # Chart area (weight graph)
    # ----------------------------
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

    # ----------------------------
    # Update weight graph
    # ----------------------------
    def refresh_chart():
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

        # Handle case where no data exists
        if not ys or not labels:
            # Provide a default empty chart or placeholder values
            weight_chart.left_axis = ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=0, label=ft.Text("0", size=12))],
                labels_interval=1,
                labels_size=40,
            )

            weight_chart.bottom_axis = ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=0, label=ft.Text("No Data", size=12))],
                labels_interval=1,
                labels_size=32,
            )

            weight_chart.min_y = 0

            page.update()
            return

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
    def pr_group_tile(id, muscle_group, mg_image):
        BASE_COLOR = ft.Colors.BLUE_500
        HOVER_COLOR = ft.Colors.BLUE_600

        def on_hover(e):
            if e.data == "true":  # Hover ON
                e.control.bgcolor = HOVER_COLOR
                e.control.scale = 1.05
            else:  # Hover OFF
                e.control.bgcolor = BASE_COLOR
                e.control.scale = 1.0

            e.control.update()

        return ft.Container(
            width=130,
            height=130,
            padding=12,
            border_radius=18,
            bgcolor=BASE_COLOR,
            ink=True,
            ink_color=ft.Colors.WHITE,
            animate=ft.Animation(180, "easeOut"),
            on_hover=on_hover,
            on_click=lambda e, m=muscle_group: open_pr_detail_page(id, m),

            content=ft.Column(
                [
                    ft.Image(src_base64=mg_image, width=55, height=55),
                    ft.Text(muscle_group,size=15,weight=ft.FontWeight.W_600,color=ft.Colors.WHITE,text_align=ft.TextAlign.CENTER,),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
        )



    def build_pr_card():
        items = get_muscle_groups()
        rows = [items[i:i+3] for i in range(0, len(items), 3)]

        return card(
            ft.Column(
                [
                    ft.Text( "Personal Records",size=20,weight=ft.FontWeight.BOLD,style=ft.TextThemeStyle.HEADLINE_MEDIUM,),
                    ft.Divider(thickness=1),

                    *[
                        ft.Row([
                                *[pr_group_tile(m["id"],m["muscle_group"].title(),m["mg_image"],)for m in row],

                                # Fill empty spaces on last row
                                *[ft.Container(width=130, height=130, opacity=0)for _ in range(3 - len(row))]
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            spacing=12,
                        )
                        for row in rows
                    ],
                ],
                spacing=20,
            )
        )

    def pr_exercise_tile(ex_name, weight, date):
        BASE_COLOR = ft.Colors.BLUE_500
        HOVER_COLOR = ft.Colors.BLUE_600

        def on_hover(e):
            e.control.bgcolor = HOVER_COLOR if e.data == "true" else BASE_COLOR
            e.control.scale = 1.05 if e.data == "true" else 1.0
            e.control.update()

        return ft.Container(
            height=150,
            padding=12,
            border_radius=18,
            bgcolor=BASE_COLOR,
            ink=True,
            animate=ft.Animation(180, "easeOut"),
            on_hover=on_hover,

            content=ft.Column(
                [
                    # Exercise icon
                    # ft.Image(src_base64=ex_icon_base64, width=55, height=55),

                    # Exercise name
                    ft.Text(
                        "ICONS",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                    ),
                    ft.Text(
                        ex_name,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                    ),
                    ft.Text(
                        f"{weight} kg",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        date.strftime("%Y-%m-%d"),
                        size=11,
                        color=ft.Colors.WHITE70,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
        )

    def open_pr_detail_page(id, muscle_group):
        prs = get_prs_for_muscle_group(id, muscle_group)

        # Sort heaviest → lightest
        sorted_prs = sorted(
            prs.items(),
            key=lambda x: x[1]["weight"],
            reverse=True,
        )

        # --- Responsive GridView ---
        grid = ft.GridView(
            expand=True,
            runs_count=6,        
            max_extent=150,      
            spacing=10,
            run_spacing=10,
        )

        # Add tiles
        for ex_name, data in sorted_prs:
            grid.controls.append(
                pr_exercise_tile(
                    ex_name,
                    data["weight"],
                    data["date"],
                )
            )

        # Page layout
        page.views.append(
            ft.View(
                route=f"/pr/{muscle_group}",
                controls=[
                    ft.AppBar(
                        title=ft.Text(f"{muscle_group} — Personal Records"),
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: go_back(),
                        ),
                    ),

                    ft.Container(
                        padding=15,
                        expand=True,
                        content=grid,  
                    ),
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


        # Normalize dates
        def norm(d):
            if isinstance(d, str):
                try:
                    return datetime.date.fromisoformat(d)
                except ValueError:
                    return datetime.datetime.fromisoformat(d).date()
            return d

        lw, a7, max_w, min_w= compute_stats()

        last_weight_label.value = f"{lw} kg" if lw else "-"
        avg7_label.value = f"{a7:.2f} kg" if a7 else "-"
        max_weights_label.value = f"{max_w:.2f} kg" if max_w else "-"
        min_weights_label.value = f"{min_w:.2f} kg" if min_w else "-"
        dropdown_api.set_options(muscle_options)
        dropdown_api.clear()

        exercise_dropdown_api.set_options([])
        exercise_dropdown_api.clear()

        dropdown_api.refresh()
        exercise_dropdown_api.refresh()
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
                            save_weight_btn,
                        ]
                    )
                )
        stats_entry4 = card(
                    ft.Column(
                        [
                            ft.Text("Log Cardio", weight=ft.FontWeight.BOLD),
                            cardio_type_dd,
                            cardio_notes,
                            time_row,
                            save_cardio_btn,
                        ]
                    )
                )
        stats_entry3 = card(
                    ft.Column(
                        [
                            ft.Text("Log Exercise", weight=ft.FontWeight.BOLD),
                            dropdown_control,
                            exercise_dropdown_control,
                            sets_completed_tf,
                            add_set_btn,
                            sets_container,
                            ex_notes,
                            save_exercise_btn,
                        ]
                    )
                )
            
        stats_column.controls.append(stats_entry1)
        stats_column.controls.append(stats_entry2)
        stats_column.controls.append(stats_entry4)
        stats_column.controls.append(stats_entry3)


        page.update()

    weight_history_btn = ft.FilledButton(
        "Weight History",
        icon=ft.Icons.SCALE,
        on_click=lambda e: open_weight_history_page()
    )

    exercise_history_btn = ft.FilledButton(
        "Exercise History",
        icon=ft.Icons.FITNESS_CENTER,
        on_click=lambda e: open_exercise_history_page()
    )

    main_history_buttons = ft.Row(
        [
            weight_history_btn,
            exercise_history_btn
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )
    
    def open_weight_history_page():
        start_date = ft.DatePicker()
        end_date = ft.DatePicker()

        page.overlay.append(start_date)
        page.overlay.append(end_date)

        results_column = ft.GridView(expand=True,runs_count=6,max_extent=150,spacing=5,run_spacing=10,)

        def load_weight_history(days=7):
            results_column.controls.clear()
            today = datetime.date.today()
            from_date = today - datetime.timedelta(days=days)

            w = list_weights_date(from_date, today)

            for r in w:
                d = r["date"]
                if isinstance(d, str):
                    try:
                        d = datetime.date.fromisoformat(d)
                    except:
                        d = datetime.datetime.fromisoformat(d).date()

                if d >= from_date:
                    results_column.controls.append(
                        card(
                            ft.Column(
                                [
                                    ft.Text(f"{r['weight_kg']} kg", size=20, weight=ft.FontWeight.BOLD),
                                    ft.Text(str(d), size=12, color=ft.Colors.GREY),
                                    ft.Text(r.get("notes", ""), size=12, italic=True),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                        )
                    )

            page.update()

        load_weight_history(7)

        def filter_range(e):
            if start_date.value and end_date.value:

                # --- FIX START: Normalize start date --- #
                raw_s = start_date.value
                if isinstance(raw_s, datetime.datetime):
                    s = raw_s.date()
                elif isinstance(raw_s, datetime.date):
                    s = raw_s
                else:
                    s = datetime.date.fromisoformat(raw_s)
                raw_e = end_date.value
                if isinstance(raw_e, datetime.datetime):
                    ed = raw_e.date()
                elif isinstance(raw_e, datetime.date):
                    ed = raw_e
                else:
                    ed = datetime.date.fromisoformat(raw_e)


                results_column.controls.clear()
                w = list_weights_date(s, ed)\

                for r in w:
                    d = r["date"]

                    if isinstance(d, datetime.datetime):
                        d = d.date()
                    elif isinstance(d, str):
                        try:
                            d = datetime.date.fromisoformat(d)
                        except:
                            d = datetime.datetime.fromisoformat(d).date()
                    elif isinstance(d, datetime.date):
                        pass
                    else:
                        continue

                    d = datetime.date(d.year, d.month, d.day)

                    if s <= d <= ed:
                        results_column.controls.append(
                            card(
                                ft.Column(
                                    [
                                        ft.Text(f"{r['weight_kg']} kg", size=20, weight=ft.FontWeight.BOLD),
                                        ft.Text(str(d), size=12, color=ft.Colors.GREY),
                                        ft.Text(r.get("notes", ""), size=12, italic=True),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                            )
                        )
                page.update()
        
        def clear_filter():
            start_date.value = None
            end_date.value = None

            load_weight_history(7)

            page.update()

        page.views.append(
            ft.View(
                "/weight_history",
                [
                    ft.AppBar(
                        title=ft.Text("Weight History"),
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: go_back(),
                        ),
                        bgcolor=ft.Colors.BLUE_500
                    ),

                    ft.Row(
                        [
                            ft.FilledButton(
                                "Start",
                                icon=ft.Icons.CALENDAR_MONTH,
                                on_click=lambda e: (setattr(start_date, "open", True), page.update()),
                            ),
                            ft.FilledButton(
                                "End",
                                icon=ft.Icons.DATE_RANGE,
                                on_click=lambda e: (setattr(end_date, "open", True), page.update()),
                            ),
                            ft.FilledButton(
                                "Filter",
                                icon=ft.Icons.FILTER_ALT,
                                on_click=filter_range,
                            ),
                            ft.FilledButton(
                                "Clear",
                                icon=ft.Icons.CLEAR_ALL,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.RED_400,
                                ),
                                on_click=lambda e: clear_filter(),
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(),

                    ft.Text("Last 7 Days", size=18, weight=ft.FontWeight.BOLD),

                    results_column,
                ]
            )
        )

        page.go("/weight_history")

    selected_context = {
        "date": None,
        "mg_id": None,
        "mg_name": None,
    }
    
    history_state = {
        "mode": "default",
        "start": None,
        "end": None,
    }

    def open_exercise_history_page():
        start_date = ft.DatePicker()
        end_date = ft.DatePicker()

        page.overlay.append(start_date)
        page.overlay.append(end_date)

        # ---------------------------
        # Animated screen switcher
        # ---------------------------
        screen_switcher = ft.AnimatedSwitcher(
            content=ft.Container(),
            expand=True,
            duration=350,
            transition=ft.AnimatedSwitcherTransition.FADE,
        )

        results_column = ft.GridView(
            expand=True,
            runs_count=6,          
            max_extent=200,        
            spacing=5,
            run_spacing=10,
        )   

        # ---------------------------
        # Tile: Muscle Group
        # ---------------------------
        def muscle_group_tile(mg_id, muscle_group, mg_image, date):
            BASE = ft.Colors.BLUE_500
            HOVER = ft.Colors.BLUE_600

            def on_hover(e):
                e.control.bgcolor = HOVER if e.data == "true" else BASE
                e.control.scale = 1.05 if e.data == "true" else 1.0
                e.control.update()

            def on_click(e):
                selected_context.update({
                    "mg_id": mg_id,
                    "mg_name": muscle_group,
                    "date": date,
                })
                show_exercises_for_day()

            return ft.Container(
                width=150,
                height=150,
                bgcolor=BASE,
                border_radius=18,
                padding=12,
                ink=True,
                animate=ft.Animation(180, "easeOut"),
                on_hover=on_hover,
                on_click=on_click,
                content=ft.Column(
                    [
                        
                        ft.Image(src_base64=mg_image, width=55, height=55),
                        ft.Text(
                            muscle_group.title(),
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            date.strftime("%Y-%m-%d"),
                            size=11,
                            color=ft.Colors.WHITE70,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
            )
        
        # ---------------------------
        # Show exercises (animated)
        # ---------------------------
        def show_exercises_for_day():
            mg_id = selected_context["mg_id"]
            date = selected_context["date"]
            mg_name = selected_context["mg_name"]

            exercises = list_mg_exercises_date(mg_id, date)

            column = ft.GridView(
                expand=True,
                runs_count=6,          
                max_extent=200,        
                spacing=5,
                run_spacing=10,
            )   

            for r in exercises:
                sets_txt = "\n".join(
                    [f"{i+1}. {s['reps']} reps @ {s['weight']}kg"
                    for i, s in enumerate(r["sets"])]
                )
                pr_flag = " 🏆" if r["is_pr"] else ""

                column.controls.append(
                        card(
                            ft.Column(
                                [
                                    # ft.Image(src_base64=mg_image, width=55, height=55),
                                    ft.Text(f"{r['name']}{pr_flag}", size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text(sets_txt, size=12),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            )
                        )
                    )

            screen_switcher.content = ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                on_click=lambda e: restore_previous_list()
                            ),
                            ft.Text(
                                f"{mg_name.title()} -  {date}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    column,
                ],
                expand=True,
            )
            page.update()

        # ---------------------------------------
        # Load last N days
        # ---------------------------------------
        def load_ex_history(days=7):
            history_state["mode"] = "default"
            history_state["start"] = None
            history_state["end"] = None

            results_column.controls.clear()
            today = datetime.date.today()
            from_date = today - datetime.timedelta(days=days)
            mg = list_muscle_group_date(from_date, today)


            for r in mg:
                d = r["date"]

                # Normalize date
                if isinstance(d, str):
                    try:
                        d = datetime.date.fromisoformat(d)
                    except:
                        d = datetime.datetime.fromisoformat(d).date()

                if d >= from_date:
                    results_column.controls.append(
                        muscle_group_tile(
                            r["id"],
                            r["muscle_group"],
                            r["mg_image"],
                            d,
                        )
                    )
            screen_switcher.content = results_column
            
            page.update()

        load_ex_history(7)

        # ---------------------------------------
        # Filter
        # ---------------------------------------
        def filter_range(e):
            if start_date.value and end_date.value:

                # --- FIX START: Normalize start date --- #
                raw_s = start_date.value
                if isinstance(raw_s, datetime.datetime):
                    s = raw_s.date()
                elif isinstance(raw_s, datetime.date):
                    s = raw_s
                else:
                    s = datetime.date.fromisoformat(raw_s)

                # --- FIX END: Normalize end date --- #
                raw_e = end_date.value
                if isinstance(raw_e, datetime.datetime):
                    ed = raw_e.date()
                elif isinstance(raw_e, datetime.date):
                    ed = raw_e
                else:
                    ed = datetime.date.fromisoformat(raw_e)

                history_state["mode"] = "filtered"
                history_state["start"] = s
                history_state["end"] = ed

                results_column.controls.clear()
                mg = list_muscle_group_date(s, ed)

                for r in mg:
                    d = r["date"]

                    if isinstance(d, datetime.datetime):
                        d = d.date()
                    elif isinstance(d, str):
                        try:
                            d = datetime.date.fromisoformat(d)
                        except:
                            d = datetime.datetime.fromisoformat(d).date()
                    elif isinstance(d, datetime.date):
                        pass
                    else:
                        continue

                    d = datetime.date(d.year, d.month, d.day)

                    if s <= d <= ed:

                        results_column.controls.append(
                            muscle_group_tile(
                                r["id"],
                                r["muscle_group"],
                                r["mg_image"],
                                d,
                            )
                        )
                page.update()

        def restore_previous_list():
            if history_state["mode"] == "filtered":
                s = history_state["start"]
                ed = history_state["end"]

                results_column.controls.clear()
                mg = list_muscle_group_date(s, ed)

                for r in mg:
                    d = r["date"]
                    if isinstance(d, str):
                        d = datetime.date.fromisoformat(d)

                    results_column.controls.append(
                        muscle_group_tile(
                            r["id"], r["muscle_group"], r["mg_image"], d
                        )
                    )

                screen_switcher.content = results_column
                page.update()
            else:
                load_ex_history(7)


        def clear_filter():
            start_date.value = None
            end_date.value = None

            load_ex_history(7)

            page.update()

        # ---------------------------------------
        # View
        # ---------------------------------------
        page.views.append(
            ft.View(
                "/exercise_history",
                controls=[
                    ft.AppBar(
                        title=ft.Text("Exercise History"),
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: go_back(),
                        ),
                        bgcolor=ft.Colors.BLUE_500,
                    ),

                    ft.Row(
                        [
                            ft.FilledButton(
                                "Start",
                                icon=ft.Icons.CALENDAR_MONTH,
                                on_click=lambda e: (setattr(start_date, "open", True), page.update()),
                            ),
                            ft.FilledButton(
                                "End",
                                icon=ft.Icons.DATE_RANGE,
                                on_click=lambda e: (setattr(end_date, "open", True), page.update()),
                            ),
                            ft.FilledButton(
                                "Filter",
                                icon=ft.Icons.FILTER_ALT,
                                on_click=filter_range,
                            ),
                            ft.FilledButton(
                                "Clear",
                                icon=ft.Icons.CLEAR_ALL,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.RED_400,
                                ),
                                on_click=lambda e: clear_filter(),
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(),

                    ft.Text("Last 7 Days", size=18, weight=ft.FontWeight.BOLD),

                    screen_switcher,
                ]
            )
        )

        page.go("/exercise_history")


    # ----------------------------
    # Refresh ALL UI components
    # ----------------------------
    def refresh_all():
        refresh_chart()
        refresh_timeline()
        update_calendar()

        page.update()


    # -------------------------TRIAL STARTS HERE----------------------------------
    def get_month_range(year: int, month: int):
        first_day = datetime.date(year, month, 1)

        if month == 12:
            next_month = datetime.date(year + 1, 1, 1)
        else:
            next_month = datetime.date(year, month + 1, 1)

        last_day = next_month - datetime.timedelta(days=1)
        return first_day, last_day


    # GLOBAL LISTS (will refresh every month)
    exercise_days = set()
    weight_days = set()
    cardio_days = set()


    # -----------------------------------------
    # 2.  LOAD DATA FOR WHOLE MONTH (CALL DB)
    # -----------------------------------------
    def load_month_data(first_day, last_day):
        global exercise_days, weight_days,cardio_days

        # Clear previous values
        exercise_days = set()
        weight_days = set()
        cardio_days = set()


        # ---- Call your DB functions ----
        exercise_records = list_exercises_date(first_day, last_day)
        weight_records   = list_weights_date(first_day, last_day)
        cardio_records   = list_cardio_date(first_day, last_day)


        # ---- Convert DB dates into sets of day numbers ----
        for ex in exercise_records:
            dt = datetime.date.fromisoformat(ex["date"]).day
            exercise_days.add(dt)

        for w in weight_records:
            dt = datetime.date.fromisoformat(w["date"]).day
            weight_days.add(dt)
        
        for c in cardio_records:
            dt = datetime.date.fromisoformat(c["date"]).day
            cardio_days.add(dt)


    # ------------------------------
    # 3.  ICON FOR A SINGLE DAY
    # ------------------------------
    def get_day_icon(day):
        global exercise_days, weight_days,cardio_days
        if day in exercise_days and day in weight_days and day in cardio_days:
            return ft.Text("✔️",size=16,tooltip="Gym workout + Cardio + Weight measurement",)
        elif  day in exercise_days and day in cardio_days:
            return ft.Text("🔥",size=16,tooltip="Gym workout + Cardio",)
        elif day in exercise_days and day in weight_days:
            return ft.Text("💪",size=16,tooltip="Gym workout + Weight measurement",)
        elif day in weight_days and day in cardio_days:
            return ft.Text("⚡",size=16,tooltip="Cardio + Weight measurement",)
        elif day in exercise_days:
            return ft.Text("🏋️",size=16,tooltip="Gym workout",)
        elif day in weight_days:
            return ft.Text("⚖️",size=16,tooltip="Weight measurement",)
        elif day in cardio_days:
            return ft.Text("🏃",size=16,tooltip="Cardio",)
        return None


    # ------------------------------
    # 4.  BUILD CALENDAR UI
    # ------------------------------
    def build_calendar(year, month):
        cal = calendar.monthcalendar(year, month)
        rows = []

        for week in cal:
            r = ft.Row(spacing=5)
            for day in week:
                if day == 0:
                    r.controls.append(ft.Container(width=45, height=45))
                else:
                    icon = get_day_icon(day)

                    controls = [
                        ft.Text(str(day), size=13, weight=ft.FontWeight.BOLD)
                    ]

                    if icon:
                        controls.append(icon)
                    r.controls.append(
                        ft.Container(
                            width=45,
                            height=45,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.BLACK12),
                            alignment=ft.alignment.center,
                            content=ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=0,
                                controls=controls,
                            ),
                        )
                    )
            rows.append(r)
        return rows


    # ------------------------------
    # 5.  UPDATE CALENDAR MONTH
    # ------------------------------
    def update_calendar():
        nonlocal current_year, current_month

        # Compute first/last day
        first_day, last_day = get_month_range(current_year, current_month)

        # ---- LOAD DATA FROM DATABASE ----
        load_month_data(first_day, last_day)

        # Build UI
        cal_column = ft.Column()
        for row in build_calendar(current_year, current_month):
            cal_column.controls.append(row)

        month_label.value = f"{calendar.month_name[current_month]} {current_year}"
        cal_switcher.content = cal_column
        page.update()


    # ------------------------------
    # 6.  MONTH NAVIGATION
    # ------------------------------
    def prev_month(e):
        nonlocal current_month, current_year
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1
        update_calendar()

    def next_month(e):
        nonlocal current_month, current_year
        current_month += 1
        if current_month == 13:
            current_month = 1
            current_year += 1
        update_calendar()


    # ------------------------------
    # 7.  INITIAL SETUP
    # ------------------------------
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month

    cal_switcher = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=400,
    )

    month_label = ft.Text(size=24, weight="bold")

    calendar_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=prev_month),
            month_label,
            ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=next_month),
        ]
    )

    update_calendar()



    def bmi_calculator():

        result_text = ft.Text(size=22, weight=ft.FontWeight.BOLD)
        category_text = ft.Text(size=16)

        height_tf = ft.TextField(
            label="Height (cm)",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.HEIGHT,
            width=300,
        )

        weight_tf = ft.TextField(
            label="Weight (kg)",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.MONITOR_WEIGHT,
            width=300,
        )

        result_card = ft.Container(
            padding=20,
            border_radius=16,
            bgcolor=ft.Colors.BLUE_500,
            animate=ft.Animation(300, "easeOut"),
            content=ft.Column(
                [result_text, category_text],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            visible=False,
        )

        # -------------------------
        # Event handler (CORRECT)
        # -------------------------
        def on_calculate_bmi(e):
            try:
                height_cm = float(height_tf.value)
                weight = float(weight_tf.value)

                height_m = height_cm / 100
                bmi = round(weight / (height_m ** 2), 1)

                if bmi < 18.5:
                    category = "Underweight"
                    color = ft.Colors.BLUE_400
                elif bmi < 25:
                    category = "Normal"
                    color = ft.Colors.GREEN_500
                elif bmi < 30:
                    category = "Overweight"
                    color = ft.Colors.ORANGE_500
                else:
                    category = "Obese"
                    color = ft.Colors.RED_500

                result_text.value = f"BMI: {bmi}"
                result_text.color = color
                category_text.value = category
                category_text.color = color

                result_card.visible = True
                result_card.opacity = 1
                result_card.update()

            except Exception:
                result_text.value = "Invalid input"
                result_text.color = ft.Colors.RED_500
                category_text.value = ""
                result_card.visible = True

            page.update()

         # -------- Clear handler --------
        def on_clear(e):
            height_tf.value = ""
            weight_tf.value = ""
            result_text.value = ""
            category_text.value = ""
            result_card.visible = False
            page.update()

        calculate_btn = ft.FilledButton(
            "Calculate BMI",
            icon=ft.Icons.CALCULATE,
            on_click=on_calculate_bmi,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=14),
                padding=16,
            ),
        )

        clear_btn = ft.OutlinedButton(
            "Clear",
            icon=ft.Icons.CLEAR,
            on_click=on_clear,
        )

        # ✅ IMPORTANT: RETURN the layout
        return ft.Column(
            [
                ft.Text("BMI Calculator", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Check your Body Mass Index",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Container(height=10),
                height_tf,
                weight_tf,
                ft.Container(height=10),
                ft.Row(
                    [calculate_btn, clear_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                ft.Container(height=20),
                result_card,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )
    
    main_bmi_buttons = ft.Container(
        content=bmi_calculator(),
        alignment=ft.alignment.center,
        width=400,   # constrain width
    )
    # -------------------------TRIAL ENDS HERE------------------------------------

    # ----------------------------
    # Responsive Layout
    # ----------------------------
    def rebuild_layout():
        page.controls.clear()
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


        # LEFT PANEL 
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
                card(main_history_buttons),
                card(calendar_row),
                card(cal_switcher),
                card(main_bmi_buttons),
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
                    card(ft.Column([ft.Text("Log Cardio", weight=ft.FontWeight.BOLD),cardio_type_dd,cardio_notes,time_row,save_cardio_btn,]), padding=12),
                    card(ft.Column([ft.Text("Log Exercise", weight=ft.FontWeight.BOLD), dropdown_api.control(),exercise_dropdown_api.control(), sets_completed_tf, add_set_btn, sets_container, ex_notes,save_exercise_btn,]), padding=12), 
                    card(main_history_buttons, padding=12),
                    card(main_bmi_buttons),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            )
            page.add(col)
        else:
            # Desktop/tablet: 3-column layout
            left_col = ft.Container(left_panel, width=430)
            center_col = ft.Container(center_panel, width=625, padding=6)
            right_col = ft.Container(right_panel, width=400, padding=6)

            main_row = ft.Row([left_col, center_col, right_col], expand=True, spacing=12) # , right_col
            page.add(top_row, ft.Divider(height=8), main_row)


        refresh_all()
        page.update()

    rebuild_layout()
