from nautobot.ipam.models import Namespace
from nautobot.apps.jobs import Job, register_jobs

name = "Change Namespace Display"


class ChangeNamespace(Job):
        
    class Meta:
        name = "Change Namespace Display"
        description = "Changes the display name to clean up Namespaces"

    namespace_list = Namespace.objects.filter(name__contains="TEST")

    def run(self, namespace_list):
        for namespace in self.namespace_list:
            new_name = namespace.name.replace("TEST", "NEW")
            namespace.name = new_name
            namespace.validated_save()  # Important: Save the changes to the database
            self.logger.info(f"Updated namespace: {namespace.name}")

register_jobs(ChangeNamespace)





