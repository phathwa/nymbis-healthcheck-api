"""AWS EC2 health check helpers."""

import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from exceptions import InstanceNotFoundError

FAILED_STATUS_CODES = {"failed", "impaired"}


def create_ec2_client():
    """Create a boto3 EC2 client.

    Returns:
        botocore.client.EC2: Configured EC2 client.
    """
    region_name = os.getenv("AWS_REGION", "eu-west-1")

    return boto3.client("ec2", region_name=region_name)


def derive_health_status(instance_state, status_code):
    """Derive a human-readable health status.

    Args:
        instance_state (str): EC2 instance state.
        status_code (str): EC2 status check result.

    Returns:
        str: Human-readable health status.
    """
    if instance_state == "running" and status_code == "ok":
        return "healthy"

    if instance_state == "running" and status_code == "initializing":
        return "initializing"

    if instance_state == "running" and status_code in FAILED_STATUS_CODES:
        return "unhealthy"

    if instance_state == "stopped":
        return "stopped"

    if instance_state == "terminated":
        return "terminated"

    return "unknown"


def get_instance_state(ec2_client, instance_id):
    """Get the current state of an EC2 instance.

    Args:
        ec2_client: boto3 EC2 client.
        instance_id (str): EC2 instance ID.

    Returns:
        str: EC2 instance state.

    Raises:
        InstanceNotFoundError: If the instance does not exist.
        ClientError: If AWS returns another client error.
    """
    try:
        response = ec2_client.describe_instances(
            InstanceIds=[instance_id],
        )
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code")

        if error_code in {
            "InvalidInstanceID.NotFound",
            "InvalidInstanceID.Malformed",
        }:
            raise InstanceNotFoundError("Instance not found") from error

        raise

    reservations = response.get("Reservations", [])

    if not reservations:
        raise InstanceNotFoundError("Instance not found")

    instances = reservations[0].get("Instances", [])

    if not instances:
        raise InstanceNotFoundError("Instance not found")

    return instances[0].get("State", {}).get("Name", "unknown")


def get_instance_status_code(ec2_client, instance_id):
    """Get the EC2 instance status check result.

    Args:
        ec2_client: boto3 EC2 client.
        instance_id (str): EC2 instance ID.

    Returns:
        str: EC2 instance status check result.
    """
    response = ec2_client.describe_instance_status(
        InstanceIds=[instance_id],
        IncludeAllInstances=True,
    )

    statuses = response.get("InstanceStatuses", [])

    if not statuses:
        return "unknown"

    instance_status = statuses[0].get("InstanceStatus", {})

    return instance_status.get("Status", "unknown")


def get_instance_health(instance_id):
    """Get health details for an EC2 instance.

    Args:
        instance_id (str): EC2 instance ID.

    Returns:
        dict: EC2 state, status code, and derived health value.

    Raises:
        InstanceNotFoundError: If the instance does not exist.
        BotoCoreError: If boto3 fails.
        ClientError: If AWS returns an unexpected client error.
    """
    try:
        ec2_client = create_ec2_client()
        instance_state = get_instance_state(ec2_client, instance_id)
        status_code = get_instance_status_code(ec2_client, instance_id)

        return {
            "state": instance_state,
            "status_code": status_code,
            "health": derive_health_status(instance_state, status_code),
        }
    except InstanceNotFoundError:
        raise
    except (BotoCoreError, ClientError):
        raise
