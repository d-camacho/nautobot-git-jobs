# from nautobot.ipam.models import Prefix, Namespace
# from nautobot.apps.jobs import Job, register_jobs

# name = "Prefix Namespace Update"

# class PrefixNamespaceUpdate(Job):

#     class Meta:
#         name = "Prefix Namespace Update"
#         description = "Updates the namespace of prefixes based on tenant"

#     def run(self):
#         # Get all prefixes with the namespace containing "Cleanup"
#         prefix_list = Prefix.objects.filter(namespace__name__contains="Cleanup")

        
#         for prefix in prefix_list:
#             # parse its tenant to match with new namespace
#             tenant = prefix.tenant
#             if not tenant:
#                 self.logger.warning(f"Prefix {prefix} has no associated tenant.")
#                 continue
#             new_namespace = Namespace.objects.filter(name=tenant).first()
#             if not new_namespace:
#                 self.logger.warning(f"No namespace found for tenant {tenant}.")
#                 continue
#             prefix.namespace = new_namespace
#             prefix.validated_save()
#             self.logger.info(f"Updated prefix {prefix} namespace to {new_namespace}")

# register_jobs(PrefixNamespaceUpdate)


from nautobot.ipam.models import Prefix, Namespace
from nautobot.apps.jobs import Job, register_jobs

name = "Prefix Namespace Update"

class PrefixNamespaceUpdate(Job):

    class Meta:
        name = "Prefix Namespace Update"
        description = "Updates the namespace of prefixes based on tenant"

    def run(self):
        # Get all prefixes with the namespace containing "Cleanup"
        prefix_list = Prefix.objects.filter(namespace__name__contains="Cleanup").select_related("tenant", "namespace")

        # Cache namespaces by tenant name to reduce database queries
        namespace_cache = {}

        for prefix in prefix_list:
            try:
                tenant = prefix.tenant
                if not tenant:
                    self.logger.warning(f"Prefix {prefix} has no associated tenant.")
                    continue

                # Check if the namespace is already cached
                if tenant.name not in namespace_cache:
                    namespace_cache[tenant.name] = Namespace.objects.filter(name=tenant.name).first()

                new_namespace = namespace_cache[tenant.name]
                if not new_namespace:
                    self.logger.warning(f"No namespace found for tenant {tenant.name}.")
                    continue

                # Update the prefix namespace
                prefix.namespace = new_namespace
                prefix.validated_save()
                self.logger.info(f"Updated prefix {prefix} namespace to {new_namespace.name}")

            except Exception as e:
                self.logger.error(f"Error updating prefix {prefix}: {e}")

register_jobs(PrefixNamespaceUpdate)

                            