import logging

from pydoover import ui


def construct_ui(processor):


    ui_elems = (
        create_multiplot(),
        ui.AlertStream("significantEvents", "Notify me of any problems"),
        ui.StateCommand("pumpMode", "Pump Mode", 
            user_options=[
                ui.Option("off", "Off"),
                ui.Option("on", "On Forever"),
                ui.Option("schedule", "Schedule"),
                ui.Option("autoLevel", "Tank Level"),
                ui.Option("autoLevelSchedule", "Tank Level + Schedule"),
            ],
        ),
        ui.Action("fillOnce", "Start Now", colour="green", requires_confirm=True),
        ui.Action("stopNow", "Stop Now", colour="red", requires_confirm=False),
        ui.BooleanVariable("pumpState", "Pump Running"),
        ui.NumericVariable("pumpPressure", "Pump Pressure (bar)", 
            dec_precision=2,
            form=ui.Widget.radial,
            ranges=[
                ui.Range("Low", 0, 1, ui.Colour.blue),
                ui.Range("Pumping", 1, 3, ui.Colour.green),
                ui.Range("High", 3, 4, ui.Colour.yellow),
            ]
        ),
        
        ui.Submodule("levelSettingsSubmodule", "Level Settings",
            children=[
                ui.StateCommand("targetSensor", "Tank Sensor",
                    user_options=[
                        ui.Option("tank1", "Tank 1"),
                        ui.Option("tank2", "Tank 2"),
                        ui.Option("tank3", "Tank 3"),
                    ],
                ),
                ui.NumericVariable(
                    "targetTankLevel",
                    "Tank Level",
                    dec_precision=0,
                    ranges=[
                        ui.Range("Start", 0, 50, ui.Colour.yellow),
                        ui.Range("", 50, 90, ui.Colour.blue),
                        ui.Range("Stop", 90, 100, ui.Colour.green),
                    ]
                ),
                ui.Slider(
                    "tankLevelTriggers", "Tank Level Triggers (%)",
                    min_val=0, max_val=100, step_size=1, dual_slider=True,
                    inverted=True, icon="fa-regular fa-tank-water", show_activity=True,
                    default_val=[50, 90]
                ),
                ui.Slider("levelAlert", "Alert Me At (%)", 
                    min_val=0, max_val=100, step_size=1, dual_slider=False,
                    inverted=False, icon="fa-regular fa-bell", show_activity=True,
                    default_val=40
                ),
                ui.Slider("runtimeAlert", "Alert Me If Pump Runs Longer Than (hrs)", 
                    min_val=0, max_val=50, step_size=1, dual_slider=False,
                    inverted=False, icon="fa-regular fa-bell", show_activity=True,
                    default_val=12
                )
            ]
        ),
        ui.Submodule("scheduleSubmodule", "Schedule",
            children=[
                ui.RemoteComponent(
                    name="scheduler",
                    display_name="Scheduler",
                    component_url="SchedulerComponent"
                ),
            ]
        ),
        ui.ConnectionInfo(name="connectionInfo",
            connection_type=ui.ConnectionType.periodic,
            connection_period=processor.get_connection_period(),
            next_connection=processor.get_connection_period(),
            offline_after=(4 * processor.get_connection_period()),
            allowed_misses=4,
        )
    )

    return ui_elems


def create_multiplot():

    ## Define overview plot series
    overview_plot_series = [
        "targetTankLevel",
        "pumpState",
    ]
    overview_plot_colours = [
        "blue",
        "tomato",
    ]
    overview_plot_active = [
        True,
        False,
    ]

    multiplot = ui.Multiplot("overviewPlot", "Overview",
        series=overview_plot_series,
        series_colours=overview_plot_colours,
        series_active=overview_plot_active,
    )

    return multiplot