"""board URL configuration."""

from django.urls import path, include

from .toolkit import views

from . import (
    api_dir, calculate_cycle, dt_potok, excel_phase_count,
    excel_sg_count_model, phase_control, restart_web_admin,
    views, openpyxl, crcpeek, swarco_log,
    get_firmware, swarco_ssh
)
from .toolkit.views import (
    ControllerManagementAPI,
    DownloadConfig,
    TrafficLightsUpdate,
    ManageControllers,
    SearchByNumberTrafficLightsAPIVeiw,
    CompareGroups,
    CompareGroupsAPI,
    PotokTrafficLightsConfigurator,
    PotokTrafficLightsConfiguratorAPI,
    ConflictsAndStagesAPI,
    ConflictsAndStages, PeekProcesses
)
from .toolkit.routers import router_controller_managemet


app_name = "tools"

urlpatterns = [
    path("", api_dir.api_dir, name="api_dir"),
    path("tools", views.tools, name="tools"),
    path(
        "calculate_cycle/",
        calculate_cycle.calculate_cycle,
        name="calculate_cycle",
    ),
    path(
        "phase_control/",
         phase_control.phase_control,
         name="phase_control"
    ),
    path(
        "restart_web_admin/",
        restart_web_admin.restart_web_admin,
        name="restart_web_admin",
    ),
    path(
        "excel_phase_count/",
        excel_phase_count.excel_phase_count,
        name="excel_phase_count",
    ),
    path(
        "excel_sg_count_model/",
        excel_sg_count_model.excel_sg_count_model,
        name="excel_sg_count_model",
    ),
    path("api/restart_web_admin/", restart_web_admin.restart_web_admin_api, name="restart_web_admin_api"),
    path("api_dir/", api_dir.api_dir, name="api_dir"),
    path("swarco_ssh/", swarco_ssh.swarco_ssh, name="swarco_ssh"),
    path('execute_top/', swarco_ssh.execute_top, name='execute_top'),
    path('execute_ps/', swarco_ssh.execute_ps, name='execute_ps'),
    path('execute_kill/', swarco_ssh.execute_kill, name='execute_kill'),
    path("dt_potok/", dt_potok.dt_potok, name="dt_potok"),
    path('dt_potok_api/', dt_potok.dt_potok_api, name='dt_potok_api'),
    path('get_phase/', phase_control.get_phase, name='get_phase'),
    path('set_phase/', phase_control.set_phase, name='set_phase'),

    path('openpyxl/', openpyxl.openpyxl, name='openpyxl'),
    path('crcpeek/', crcpeek.crcpeek, name='crcpeek'),
    path('swarco_log/', swarco_log.swarco_log, name='swarco_log'),
    path('get_firmware/', get_firmware.get_firmware, name='get_firmware'),
    path('get_firmware_api/', get_firmware.get_firmware_api, name='get_firmware_api'),

    path("manage_controllers/", ManageControllers.as_view(), name='manage_controllers'),
    path("download_config/", DownloadConfig.as_view(), name='download_config'),
    path('calc_conflicts/', ConflictsAndStages.as_view(), name='calc_conflicts'),
    path("passport/", CompareGroups.as_view(), name="passport"),
    path("tlc_potok/", PotokTrafficLightsConfigurator.as_view(), name="tlc_potok"),
    path("api/v1/manage-controller/", ControllerManagementAPI.as_view()),
    path("api/v1/download-config/", ControllerManagementAPI.as_view()),
    path("api/v1/conflicts/", ConflictsAndStagesAPI.as_view()),
    path('api/v1/trafficlight-objects/<str:number>', SearchByNumberTrafficLightsAPIVeiw.as_view()),
    path('api/v1/update_trafficlihgtdata/', TrafficLightsUpdate.as_view()),
    path("api/v1/compare-groups/", CompareGroupsAPI.as_view()),
    path("api/v1/potok-tlc/", PotokTrafficLightsConfiguratorAPI.as_view()),
    path("api/v1/peek-processes/", PeekProcesses.as_view()),
    path("api/v1/", include(router_controller_managemet.urls)),
]
