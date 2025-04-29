from nautobot.ipam.models import Namespace
from nautobot.apps.jobs import Job, register_jobs

name = "Change Namespace Display"


class ChangeNamespace(Job):
        
    class Meta:
        name = "Change Namespace Display"
        description = "Changes the display name to clean up Namespaces"

    def run(self):
        self.namespace_object = Namespace.objects.get(id="f5019028-3bdb-4fe7-a957-eb65f93405bd")
        if self.namespace_object:
            self.namespace_object.name = "TEST1"
            self.namespace_object.save()
        else:
            self.logger.info("Namespace id not available")

register_jobs(ChangeNamespace)