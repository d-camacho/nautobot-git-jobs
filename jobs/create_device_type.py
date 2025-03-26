import re
import yaml
from itertools import product
from django.db import transaction
from nautobot.apps.jobs import Job, BooleanVar
from nautobot.dcim.models import DeviceType, Manufacturer
from nautobot.dcim.models.device_component_templates import InterfaceTemplate

name = "Create Device Types"

DEVICE_TYPES_YAML = [
    """
    manufacturer: Arista
    model: DCS-7280CR2-60
    part_number: DCS-7280CR2-60
    u_height: 1
    is_full_depth: true
    comments: '[Arista 7280R Data Sheet](https://www.arista.com/assets/data/pdf/Datasheets/7280R-DataSheet.pdf)'
    interfaces:
        - pattern: "Ethernet[1-60]/[1-4]"
          type: 100gbase-x-qsfp28
        - pattern: "Management1"
          type: 1000base-t
          mgmt_only: true
    """,
    """
    manufacturer: Arista
    model: DCS-7150S-24
    part_number: DCS-7150S-24
    u_height: 1
    is_full_depth: true
    comments: '[Arista 7150 Data Sheet](https://www.arista.com/assets/data/pdf/Datasheets/7150S_Datasheet.pdf)'
    interfaces:
        - pattern: "Ethernet[1-24]"
          type: 10gbase-x-sfpp
        - pattern: "Management1"
          type: 1000base-t
          mgmt_only: true
    """,
    """
    manufacturer: Cisco
    model: Nexus N9K-C9236C
    part_number: N9K-C9236C
    u_height: 1
    is_full_depth: true
    interfaces:
        - pattern: "Ethernet1/[1-48]"
          type: 100gbase-x-qsfp28
        - pattern: "mgmt0"
          type: 1000base-t
          mgmt_only: true
    """,
]


def expand_interface_pattern(pattern):
    """
    Expands an interface pattern into actual names with enhanced validation.
    """
    match = re.findall(r"\[([0-9]+)-([0-9]+)\]", pattern)
    if not match:
        return [pattern]

    try:
        ranges = [list(range(int(start), int(end) + 1)) for start, end in match]
    except ValueError as e:
        raise ValueError(f"Invalid range in pattern {pattern}: {e}") from e

    # Validate range order
    for start, end in match:
        if int(start) >= int(end):
            raise ValueError(f"Invalid range {start}-{end} in {pattern}")

    base_name = re.sub(r"\[[0-9]+-[0-9]+\]", "{}", pattern, count=len(ranges))
    return [base_name.format(*nums) for nums in product(*ranges)]

def create_device_types(logger, dryrun=False):
    """
    Creates DeviceType objects with transaction support and bulk operations.
    """
    with transaction.atomic():
        # Create savepoint if dryrun
        sid = transaction.savepoint() if dryrun else None

        for device_yaml in DEVICE_TYPES_YAML:
            try:
                data = yaml.safe_load(device_yaml)
            except yaml.YAMLError as e:
                logger.error(f"YAML parsing error: {e}")
                continue

            # Manufacturer validation
            manufacturer_name = data.get("manufacturer")
            if not manufacturer_name:
                logger.error("Manufacturer not specified in YAML entry")
                continue
                
            manufacturer = Manufacturer.objects.filter(name=manufacturer_name).first()
            if not manufacturer:
                logger.error(f"Manufacturer '{manufacturer_name}' not found. Create it first.")
                continue

            # DeviceType handling
            model_name = data.get("model")
            if not model_name:
                logger.error(f"Missing model name for manufacturer {manufacturer_name}")
                continue

            device_type_defaults = {
                k: data.get(k) 
                for k in ["part_number", "u_height", "is_full_depth", "comments"]
            }
            device_type, created = DeviceType.objects.get_or_create(
                manufacturer=manufacturer,
                model=model_name,
                defaults=device_type_defaults
            )

            if created:
                logger.info(f"Created new DeviceType: {manufacturer.name} {model_name}")
            else:
                logger.info(f"Using existing DeviceType: {manufacturer.name} {model_name}")

            # InterfaceTemplate bulk creation
            interface_templates = []
            for iface_def in data.get("interfaces", []):
                pattern = iface_def.get("pattern")
                iface_type = iface_def.get("type")
                mgmt_only = iface_def.get("mgmt_only", False)

                if not pattern or not iface_type:
                    logger.error(f"Invalid interface definition in {model_name}: {iface_def}")
                    continue

                try:
                    interface_names = expand_interface_pattern(pattern)
                except ValueError as e:
                    logger.error(f"Interface pattern error: {e}")
                    continue

                for name in interface_names:
                    interface_templates.append(
                        InterfaceTemplate(
                            device_type=device_type,
                            name=name,
                            type=iface_type,
                            mgmt_only=mgmt_only
                        )
                    )

            if interface_templates:
                created_count = 0
                if not dryrun:
                    # Bulk create with conflict ignoring
                    results = InterfaceTemplate.objects.bulk_create(
                        interface_templates,
                        update_conflicts=False,
                        unique_fields=["device_type", "name"],
                        update_fields=[]
                    )
                    created_count = len(results)
                else:
                    created_count = len(interface_templates)
                    
                logger.info(
                    f"Processed {len(interface_templates)} interfaces for {model_name} "
                    f"({created_count} new)"
                )

        # Rollback if dryrun
        if dryrun and sid:
            transaction.savepoint_rollback(sid)

class CreateDeviceType(Job):
    """
    Creates device types from YAML definitions with dry-run support.
    """
    dryrun = BooleanVar(
        default=False,
        description="Simulate changes without writing to database"
    )

    class Meta:
        name = "Bulk Add Device Types"
        commit_default = False  # Encourage explicit saving

    def run(self, dryrun):
        self.logger.info(f"Starting device type import (dryrun: {dryrun})")
        create_device_types(self.logger, dryrun=dryrun)
        self.logger.info("Import process completed" + (" (dry run)" if dryrun else ""))