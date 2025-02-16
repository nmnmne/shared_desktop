"""board URL configuration."""
from django.urls import path

from . import views


app_name = "prog"

urlpatterns = [
    path(
        "",
        views.prog,
        name="prog"
    ),
    path(
        "passport/equipment_layout/",
        views.equipment_layout,
        name="equipment_layout"
    ),
    path(
        "passport/table_of_directions/",
        views.table_of_directions,
        name="table_of_directions"
    ),
    path(
        "passport/phase_images/",
        views.phase_images,
        name="phase_images"
    ),
    path(
        "passport/fixed_program_tables/",
        views.fixed_program_tables,
        name="fixed_program_tables"
    ),
    path(
        "passport/the_layout_of_the_detectors/",
        views.the_layout_of_the_detectors,
        name="the_layout_of_the_detectors"
    ),
    path(
        "passport/table_of_detectors/",
        views.table_of_detectors,
        name="table_of_detectors"
    ),
    path(
        "passport/monitoring_of_peripheral_equipment/",
        views.monitoring_of_peripheral_equipment,
        name="monitoring_of_peripheral_equipment"
    ),
    path(
        "passport/phase_alternation/",
        views.phase_alternation,
        name="phase_alternation"
    ),
    path(
        "passport/adaptive_program_tables/",
        views.adaptive_program_tables,
        name="adaptive_program_tables"
    ),
]
