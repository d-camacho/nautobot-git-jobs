from nautobot.apps.jobs import register_jobs
from .hello_jobs import HelloJobs
from .create_device_type import CreateDeviceType

name = "Git Repositories"

register_jobs(HelloJobs)
register_jobs(CreateDeviceType)