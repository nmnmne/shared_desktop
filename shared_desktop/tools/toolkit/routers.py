from rest_framework.routers import SimpleRouter

from tools.toolkit.views import ControllerManagementHostsConfigurationViewSetAPI

router_controller_managemet = SimpleRouter()
router_controller_managemet.register(
r'controller-management-configurations', ControllerManagementHostsConfigurationViewSetAPI,
)

