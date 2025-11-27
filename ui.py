import flet as ft
import datetime

from utils import iso_today
from models import add_weight_entry, list_weights, add_exercise, list_exercises, detect_prs
from charts import generate_weight_chart
from csv_io import export_all, import_weights, import_exercises

def build_app(page: ft.Page):
    # ---------------------------------------------------------
    # PAGE CONFIG
    # ---------------------------------------------------------
    page.title = "Fitness Tracker — Desktop Edition"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()

    # GLOBAL COMPONENTS --------------------------------------
    date_label = ft.Text("No date selected", size=13, italic=True)

    date_picker = ft.DatePicker(
        first_date=datetime.datetime(2000, 10, 1),
        on_change=lambda e: (
            date_label.__setattr__("value", date_picker.value.isoformat()),
            page.update()
        )
    )

    page.overlay.append(date_picker)

    # ---------------------------------------------------------
    # INPUT FIELDS - Weight Section
    # ---------------------------------------------------------
    weight_input = ft.TextField(label="Weight (kg)")
    weight_notes = ft.TextField(label="Notes", multiline=True)

    # ---------------------------------------------------------
    # INPUT FIELDS - Exercise Section
    # ---------------------------------------------------------
    ex_name = ft.TextField(label="Exercise")
    sets_completed = ft.TextField(label="Total Sets Completed", width=200)
    ex_notes = ft.TextField(label="Notes", multiline=True)
    
    sets_container = ft.Column(spacing=8)

    def add_rep_row(e=None):
        reps = ft.TextField(label="Reps", width=80)
        wt = ft.TextField(label="Weight (kg)", width=110)

        delete_btn = ft.IconButton(
            icon=ft.icons.DELETE_OUTLINE,
            icon_color="red600",
        )

        row = ft.Row(
            [reps, wt, delete_btn],
            alignment=ft.MainAxisAlignment.START,
        )

        delete_btn.on_click = lambda e: (sets_container.controls.remove(row), page.update())

        sets_container.controls.append(row)
        page.update()

    # ---------------------------------------------------------
    # SAVE HANDLERS
    # ---------------------------------------------------------
    def save_weight(e):
        if not date_picker.value:
            date_picker.value = datetime.date.today().isoformat()
            page.snack_bar = ft.SnackBar(ft.Text(f"Today's {date_picker.value} date selected "))
            page.snack_bar.open = True
            
            page.update()
            return

        add_weight_entry(
            date_picker.value.isoformat(),
            float(weight_input.value),
            weight_notes.value,
        )

        weight_input.value = ""
        weight_notes.value = ""

        refresh_timeline()
        refresh_chart()
        page.update()

    def save_exercise(e):
        if not date_picker.value:
            date_picker.value = datetime.date.today().isoformat()
            page.snack_bar = ft.SnackBar(ft.Text(f"Today's {date_picker.value} date selected "))
            page.snack_bar.open = True
            page.update()
            return

        sets = []
        for row in sets_container.controls:
            reps = row.controls[0].value
            wt = row.controls[1].value
            sets.append({"reps": int(reps or 0), "weight": float(wt or 0)})

        add_exercise(
            date_picker.value.isoformat(),
            ex_name.value,
            int(sets_completed.value or 0),
            sets,
            ex_notes.value,
        )

        ex_name.value = ""
        ex_notes.value = ""
        sets_completed.value = ""
        sets_container.controls.clear()

        refresh_timeline()
        refresh_chart()
        page.update()

    def clear_date(e):
        date_picker.value = None
        date_label.value = "No date selected"
        page.update()

    # ---------------------------------------------------------
    # TIMELINE PANEL (right side)
    # ---------------------------------------------------------
    timeline = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    def refresh_timeline():
        timeline.controls.clear()

        w = list_weights()
        ex = list_exercises()
        prs = detect_prs()

        combined = []
        for r in w: combined.append((r["date"], "weight", r))
        for r in ex: combined.append((r["date"], "exercise", r))
        # combined.sort()
        # FIX: sort only by date + type, never by dict
        combined.sort(key=lambda x: (x[0], x[1]))

        for d, t, r in combined:
            if t == "weight":
                card = ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(
                                    f"{r['date']} — Weight: {r['weight_kg']} kg",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(r.get("notes") or ""),
                            ]
                        ),
                        padding=15,
                    )
                )
            else:

                set_lines = [
                    f"Set {i+1}: {s['reps']} reps @ {s['weight']} kg"
                    for i, s in enumerate(r["sets"])
                ]

                # Default no PR unless sets exist
                pr_flag = ""

                if r["sets"]:   # only check PR if there are sets
                    max_set_weight = max(s["weight"] for s in r["sets"])
                    if r["name"].lower() in prs and max_set_weight == prs[r["name"].lower()]:
                        pr_flag = " 🏆"

                card = ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(
                                    f"{r['date']} — {r['name']}{pr_flag}",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(f"Sets: {r['sets_completed']}"),
                                ft.Column([ft.Text(s) for s in set_lines]),
                                ft.Text(r.get("notes") or ""),
                            ]
                        ),
                        padding=15,
                    )
                )

            timeline.controls.append(card)

        page.update()

    # ---------------------------------------------------------
    # CHART IMAGE
    # ---------------------------------------------------------

    # Create the chart control
    weight_chart = ft.LineChart(
        data_series=[],
        width=600,
        height=300,
        border=ft.border.all(3, ft.colors.with_opacity(0.2, ft.colors.ON_SURFACE)),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=1, color=ft.colors.with_opacity(0.2, ft.colors.ON_SURFACE), width=1
        ),
        vertical_grid_lines=ft.ChartGridLines(
            interval=1, color=ft.colors.with_opacity(0.2, ft.colors.ON_SURFACE), width=1
        ),
        left_axis=ft.ChartAxis(),
        bottom_axis=ft.ChartAxis(),
        tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY),
        min_y=0,
        animate=300,
        expand=True,
    )

    def refresh_chart():
        print("Refreshing chart...")

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

    # ---------------------------------------------------------
    # CSV HANDLERS
    # ---------------------------------------------------------
    file_picker = ft.FilePicker(
        on_result=lambda e: (
            import_weights(e.files[0].path) if e.files and e.files[0].path.endswith("weights.csv") else None,
            import_exercises(e.files[0].path) if e.files and e.files[0].path.endswith("exercises.csv") else None,
            refresh_timeline(),
            refresh_chart(),
            page.update(),
        )
    )
    page.overlay.append(file_picker)

    # ---------------------------------------------------------
    # LEFT SIDEBAR — FORM PANELS
    # ---------------------------------------------------------
    weight_card = ft.Card(
        ft.Container(
            ft.Column(
                [
                    ft.Text("Weight Entry", size=18, weight=ft.FontWeight.BOLD),
                    weight_input,
                    weight_notes,
                    ft.ElevatedButton("Save Weight", on_click=save_weight),
                ],
                spacing=10,
            ),
            padding=20,
        )
    )
    add_rep_row()
    exercise_card = ft.Card(
        ft.Container(
            ft.Column(
                [
                    ft.Text("Exercise Entry", size=18, weight=ft.FontWeight.BOLD),
                    ex_name,
                    sets_completed,
                    ft.ElevatedButton("Add Reps", on_click=add_rep_row),
                    sets_container,
                    ex_notes,
                    ft.ElevatedButton("Save Exercise", on_click=save_exercise),
                ],
                spacing=10,
            ),
            padding=20,
        )
    )

    sidebar = ft.Container(
        ft.Column(
            [
                ft.Text("Inputs", size=22, weight=ft.FontWeight.BOLD),
                weight_card,
                exercise_card,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
        ),
        width=360,
        padding=20,
        bgcolor=ft.colors.with_opacity(0.02, ft.colors.ON_SURFACE),
    )

    # ---------------------------------------------------------
    # TOP BAR (desktop-style)
    # ---------------------------------------------------------
    top_bar = ft.Container(
        ft.Row(
            [
                ft.Text("Fitness Tracker", size=22, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                date_label,
                ft.ElevatedButton("Clear Date", on_click=clear_date),
                ft.ElevatedButton(
                    "Pick Date",
                    icon=ft.icons.CALENDAR_MONTH,
                    on_click=lambda e: (setattr(date_picker, "open", True), page.update()),
                ),
                ft.IconButton(icon=ft.icons.DARK_MODE, on_click=toggle_theme),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
        ),
        padding=15,
        bgcolor=ft.colors.with_opacity(0.03, ft.colors.ON_SURFACE),
    )

    # ---------------------------------------------------------
    # RIGHT PANEL — TIMELINE + CHART
    # ---------------------------------------------------------
    right_panel = ft.Container(
    content=ft.Column(
        [
            ft.Text("History & Progress", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(timeline, expand=True),
            ft.Text("Weight Chart", size=18, weight=ft.FontWeight.BOLD),
            weight_chart,
        ],
        expand=True,
        spacing=20,
    ),
    expand=True,
    padding=20,
)

    # ---------------------------------------------------------
    # MAIN LAYOUT: Sidebar | Content
    # ---------------------------------------------------------
    main_layout = ft.Column(
        [
            top_bar,
            ft.Row(
                [
                    sidebar,
                    right_panel,
                ],
                expand=True,
            ),
        ],
        expand=True,
    )

    page.add(main_layout)

    refresh_timeline()
    refresh_chart()
    page.update()
