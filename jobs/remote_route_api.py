from nautobot.apps.jobs import Job, ObjectVar, StringVar, register_jobs
from nautobot.dcim.models import Device, Location
from nautobot.extras.models.secrets import Secret
from requests.auth import HTTPBasicAuth
import requests
import json


name = "API Requests"


class RemoteRouteAPI(Job):
    """Fetch routing table from Arista or Cisco devices."""

    class Meta:
        name = "Remote Route API"
        has_sensitive_variables = False
        description = "Make API calls to retrieve routing table from a device using the requests library"

    # Device location and device selection
    device_location = ObjectVar(
        model=Location, 
        required=False
    )
    
    device = ObjectVar(
        model=Device,
        query_params={
            "location": "$device_location",
        },
    )

    target_ip = StringVar(
        description="Enter destination IP or remote route. Shows all routes if left blank.", 
        required=False
    )

    def run(self, device_location, device, target_ip):
        """Main function to determine the platform and fetch routes."""
        
        # Log statements for targeted or full route checks
        if target_ip:
            self.logger.info(f"Checking if {device.name} has a route to {target_ip}.")
        else:
            self.logger.info(f"Fetching all routes from {device.name}.")

        # Verify primary IP exists
        if device.primary_ip is None:
            self.logger.fatal(f"Device '{device.name}' does not have a primary IP address set.")
            return

        # Verify platform exists
        if device.platform is None:
            self.logger.fatal(f"Device '{device.name}' does not have a platform set.")
            return

        # Identify command based on device platform
        command_map = {
            "cisco_ios": "show ip route",
            "arista_eos": "show ip route",
            "juniper_junos": "show route"
        }
        
        platform_name = device.platform.network_driver
        base_cmd = command_map.get(platform_name, None) 

        if not base_cmd:
            self.logger.fatal(f"Unsupported platform: {platform_name}")
            return

        # Append target IP if provided
        cmd = f"{base_cmd} {target_ip}" if target_ip else base_cmd

        # Extract primary IP address
        device_ip = str(device.primary_ip).split("/")[0]

        # API request setup
        headers = {"Content-Type": "application/json"}
        auth = ("admin", "admin")

        # Arista API Payload
        if platform_name == "arista_eos":
            url = f"https://{device_ip}/command-api"
            payload = {
                "jsonrpc": "2.0",
                "method": "runCmds",
                "params": {
                    "version": 1,
                    "cmds": [cmd],
                    "format": "json"
                },
                "id": 1
            }
            method = "POST"

        # Cisco API Variables (RESTCONF)
        elif platform_name == "cisco_ios":
            url = f"https://{device_ip}/restconf/data/Cisco-IOS-XE-native:native/ip/route"
            headers["Accept"] = "application/yang-data+json"
            payload = None  # Cisco RESTCONF uses GET, not POST
            method = "GET"

        # Construct and send API request
        try:
            if method == "POST":
                response = requests.post(url, json=payload, auth=auth, headers=headers, verify=False)
            else:
                response = requests.get(url, auth=auth, headers=headers, verify=False)

            response.raise_for_status()
            route_data = response.json()
            self.logger.info(f"Routing table from {device.name}:\n{json.dumps(route_data, indent=2)}")
            return route_data

        except requests.exceptions.RequestException as e:
            self.logger.fatal(f"Error connecting to {device.name}: {e}")
            return None


# Register job in Nautobot
register_jobs(RemoteRouteAPI)
