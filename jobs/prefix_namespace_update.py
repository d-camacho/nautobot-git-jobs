from nautobot.ipam.models import Prefix, Namespace
from nautobot.apps.jobs import Job, register_jobs

name = "Prefix Namespace Update"

class PrefixNamespaceUpdate(Job):

    class Meta:
        name = "Prefix Namespace Update"
        description = "Updates the namespace of prefixes based on tenant"

    def run(self):
        # Get all prefixes with the namespace containing "Cleanup"
        prefix_list = Prefix.objects.filter(namespace__name__contains="Cleanup")

        
        for prefix in prefix_list:
            # parse its tenant to match with new namespace
            tenant = prefix.tenant
            if not tenant:
                self.logger.warning(f"Prefix {prefix} has no associated tenant.")
                continue
            new_namespace = Namespace.objects.filter(name=tenant).first()
            if not new_namespace:
                self.logger.warning(f"No namespace found for tenant {tenant}.")
                continue
            prefix.namespace = new_namespace
            prefix.validated_save()
            self.logger.info(f"Updated prefix {prefix} namespace to {new_namespace}")

register_jobs(PrefixNamespaceUpdate)

                            