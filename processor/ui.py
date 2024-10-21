import logging

from pydoover import ui
from farmo_client import PumpMode


def construct_ui(processor):


    ui_elems = (
        create_multiplot(),
        # ui.AlertStream("significantEvents", "Notify me of any problems"),
        ui.BooleanVariable("pumpState", "Pump Running"),
        # ui.NumericVariable("pumpPressure", "Pump Pressure (bar)", 
        #     dec_precision=2,
        #     form=ui.Widget.radial,
        #     ranges=[
        #         ui.Range("Low", 0, 1, ui.Colour.blue),
        #         ui.Range("Pumping", 1, 3, ui.Colour.green),
        #         ui.Range("High", 3, 4, ui.Colour.yellow),
        #     ]
        # ),
        ui.StateCommand("pumpMode", "Pump Mode", 
            user_options=[
                ui.Option("off", "Off"),
                ui.Option("on_forever", "On Forever"),
                ui.Option("schedule", "Schedule"),
                ui.Option("tank_level", "Tank Level"),
                ui.Option("tank_level_schedule", "Tank Level + Schedule")
            ],
            default_val="off"
        ),
        # ui.Action("startNow", "Start Now", colour="green", requires_confirm=True),
        # ui.Action("stopNow", "Stop Now", colour="red", requires_confirm=False),
        # get_immediate_action_button(processor),
        ui.Action("startStopNow", "Start Now", colour="green", requires_confirm=True),

        ui.Submodule("levelSettingsSubmodule", "Level Settings",
            children=[
                ui.StateCommand("targetSensor", "Tank Sensor",
                    user_options=get_sensor_options(processor),
                    # user_options=[
                        # ui.Option("tank1", "Tank 1"),
                        # ui.Option("tank2", "Tank 2"),
                        # ui.Option("tank3", "Tank 3"),
                    # ],
                ),
                ui.NumericVariable(
                    "targetTankLevel",
                    "Tank Level (%)",
                    dec_precision=0,
                    ranges=get_tank_level_ranges(processor),
                ),
                ui.Slider(
                    "tankLevelTriggers", "Tank Level Triggers (%)",
                    min_val=0, max_val=100, step_size=1, dual_slider=True,
                    inverted=True, icon="fa-regular fa-tank-water", show_activity=True,
                    default_val=[50, 90],colours=["yellow","blue","green"]
                ),
                # ui.Slider("levelAlert", "Low Level Alert (%)", 
                #     min_val=0, max_val=100, step_size=1, dual_slider=False,
                #     inverted=False, icon="fa-regular fa-bell", show_activity=True,
                #     default_val=40
                # ),
                # ui.Slider("runtimeAlert", "Pump Runtime Alert (hrs)", 
                #     min_val=0, max_val=50, step_size=1, dual_slider=False,
                #     inverted=False, icon="fa-regular fa-bell", show_activity=True,
                #     default_val=12
                # )
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

        # ui.TextVariable("imei", "IMEI"),
        ui.HiddenValue("_pumpState", show_activity=False),
        ui.ConnectionInfo(name="connectionInfo",
            connection_type=ui.ConnectionType.other,
            # connection_period=processor.get_connection_period(),
            # next_connection=processor.get_connection_period(),
            # offline_after=(60 * 60), # 1 hour
            # allowed_misses=4,
        )
    )

    return ui_elems


def create_multiplot():

    ## Define overview plot series
    overview_plot_series = [
        "targetTankLevel",
        "pumpState",
        # "pumpPressure",
    ]
    overview_plot_colours = [
        "blue",
        "tomato",
        # "green",
    ]
    overview_plot_active = [
        True,
        False,
        # False,
    ]

    multiplot = ui.Multiplot("overviewPlot", "Overview",
        series=overview_plot_series,
        series_colours=overview_plot_colours,
        series_active=overview_plot_active,
    )

    return multiplot


# def get_immediate_action_button(processor):
#     if processor.get_internal_pump_state():
#         return ui.Action("stopNow", "Stop Now", colour="red", requires_confirm=False)
#     else:
#         return ui.Action("startNow", "Start Now", colour="green", requires_confirm=True)


def get_sensor_options(processor):
    sensors = processor.get_available_tank_sensors()
    options = []
    for sensor in sensors:
        options.append(ui.Option(str(sensor["IMEI"]), sensor["NAME"]))
    return options


def get_tank_level_ranges(processor):

    ## get if in pump mode
    pump_mode = processor.get_pump_mode()
    if pump_mode not in [PumpMode.TANK_LEVEL, PumpMode.TANK_LEVEL_SCHEDULE]:
        logging.info(f"Pump mode is not tank level or tank level schedule, returning None")
        return None

    ## get low and high thresholds
    result = processor.get_tank_level_triggers()
    if result is None:
        logging.info(f"No tank level triggers set, returning default")
        low_threshold = 50
        high_threshold = 90
    else:

        low_threshold, high_threshold = result

    return [
        ui.Range("Tank level will trigger pump start", 0, low_threshold, ui.Colour.yellow),
        ui.Range("", low_threshold, high_threshold, ui.Colour.blue),
        ui.Range("Tank level will trigger pump stop", high_threshold, 100, ui.Colour.green),
    ]