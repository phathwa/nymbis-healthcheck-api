"""Tests for AWS EC2 health check logic."""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from aws_health import (
    derive_health_status,
    get_instance_health,
    get_instance_state,
    get_instance_status_code,
)
from exceptions import InstanceNotFoundError


def test_derive_health_status_for_running_ok_instance():
    """Running instances with OK checks should be healthy."""
    assert derive_health_status("running", "ok") == "healthy"


def test_derive_health_status_for_running_initializing_instance():
    """Running instances with initializing checks should be initializing."""
    assert derive_health_status("running", "initializing") == "initializing"


def test_derive_health_status_for_running_failed_instance():
    """Running instances with failed checks should be unhealthy."""
    assert derive_health_status("running", "failed") == "unhealthy"


def test_derive_health_status_for_running_impaired_instance():
    """Running instances with impaired checks should be unhealthy."""
    assert derive_health_status("running", "impaired") == "unhealthy"


def test_derive_health_status_for_stopped_instance():
    """Stopped instances should return stopped health."""
    assert derive_health_status("stopped", "unknown") == "stopped"


def test_derive_health_status_for_terminated_instance():
    """Terminated instances should return terminated health."""
    assert derive_health_status("terminated", "unknown") == "terminated"


def test_get_instance_state_returns_state_name():
    """Instance state should be extracted from describe_instances."""
    ec2_client = Mock()
    ec2_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "State": {
                            "Name": "running",
                        }
                    }
                ]
            }
        ]
    }

    state = get_instance_state(ec2_client, "i-0123456789abcdef0")

    assert state == "running"


def test_get_instance_state_raises_not_found_for_empty_reservations():
    """Empty reservations should be treated as instance not found."""
    ec2_client = Mock()
    ec2_client.describe_instances.return_value = {
        "Reservations": [],
    }

    with pytest.raises(InstanceNotFoundError):
        get_instance_state(ec2_client, "i-missing")


def test_get_instance_state_raises_not_found_for_aws_not_found_error():
    """AWS not found errors should become InstanceNotFoundError."""
    ec2_client = Mock()
    ec2_client.describe_instances.side_effect = ClientError(
        {
            "Error": {
                "Code": "InvalidInstanceID.NotFound",
                "Message": "Instance not found",
            }
        },
        "DescribeInstances",
    )

    with pytest.raises(InstanceNotFoundError):
        get_instance_state(ec2_client, "i-missing")


def test_get_instance_state_reraises_unexpected_client_error():
    """Unexpected AWS client errors should not be swallowed."""
    ec2_client = Mock()
    ec2_client.describe_instances.side_effect = ClientError(
        {
            "Error": {
                "Code": "RequestLimitExceeded",
                "Message": "Rate exceeded",
            }
        },
        "DescribeInstances",
    )

    with pytest.raises(ClientError):
        get_instance_state(ec2_client, "i-0123456789abcdef0")


def test_get_instance_status_code_returns_status():
    """Instance status code should be extracted from describe_instance_status."""
    ec2_client = Mock()
    ec2_client.describe_instance_status.return_value = {
        "InstanceStatuses": [
            {
                "InstanceStatus": {
                    "Status": "ok",
                }
            }
        ]
    }

    status_code = get_instance_status_code(
        ec2_client,
        "i-0123456789abcdef0",
    )

    assert status_code == "ok"


def test_get_instance_status_code_returns_unknown_when_missing():
    """Missing status checks should return unknown."""
    ec2_client = Mock()
    ec2_client.describe_instance_status.return_value = {
        "InstanceStatuses": [],
    }

    status_code = get_instance_status_code(
        ec2_client,
        "i-0123456789abcdef0",
    )

    assert status_code == "unknown"


def test_get_instance_health_returns_combined_result():
    """Health check should combine EC2 state, status code, and health."""
    ec2_client = Mock()
    ec2_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "State": {
                            "Name": "running",
                        }
                    }
                ]
            }
        ]
    }
    ec2_client.describe_instance_status.return_value = {
        "InstanceStatuses": [
            {
                "InstanceStatus": {
                    "Status": "ok",
                }
            }
        ]
    }

    with patch("aws_health.create_ec2_client", return_value=ec2_client):
        result = get_instance_health("i-0123456789abcdef0")

    assert result == {
        "state": "running",
        "status_code": "ok",
        "health": "healthy",
    }
