from nautobot.apps.jobs import register_jobs
from .hello_jobs import HelloJobs

register_jobs(HelloJobs)