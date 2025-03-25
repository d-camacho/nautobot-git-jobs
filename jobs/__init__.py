from nautobot.apps.jobs import register_jobs
from .hello_jobs import HelloJobs
from .create_device_type import CreateDeviceType

register_jobs(HelloJobs)
register_jobs(CreateDeviceType)