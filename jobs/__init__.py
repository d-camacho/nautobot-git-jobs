from nautobot.apps.jobs import register_jobs

from .change_namespace import ChangeNamespace
from .create_device_type import CreateDeviceType
from .hello_jobs import HelloJobs
from .prefix_namespace_update import PrefixNamespaceUpdate
from .remote_route_api import RemoteRouteAPI



register_jobs(
    ChangeNamespace,
    CreateDeviceType,
    HelloJobs,
    PrefixNamespaceUpdate,
    RemoteRouteAPI,
)
