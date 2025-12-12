"""Tests for SummaryResponse model validation.

This module contains tests for verifying that the SummaryResponse model
correctly validates response data consistency based on status.
"""
import pytest
from pydantic import ValidationError

from gcrs.models import RepositorySummary, SummaryResponse


def test_summary_response_valid_error():
    """Test that a valid error response is accepted."""
    response = SummaryResponse(
        status="error",
        error="Test error message",
        repository_summary=None,
    )
    assert response.status == "error"
    assert response.error == "Test error message"
    assert response.repository_summary is None


def test_summary_response_valid_success():
    """Test that a valid success response is accepted."""
    summary = RepositorySummary()
    response = SummaryResponse(
        status="success",
        repository_summary=summary,
    )
    assert response.status == "success"
    assert response.repository_summary == summary
    assert response.error is None


def test_summary_response_success_without_summary_raises_error():
    """Test that success status without repository_summary raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SummaryResponse(
            status="success",
            repository_summary=None,
        )
    
    error_str = str(exc_info.value)
    assert "repository_summary is required when status is 'success'" in error_str


def test_summary_response_error_without_error_message_raises_error():
    """Test that error status without error message raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SummaryResponse(
            status="error",
            error=None,
        )
    
    error_str = str(exc_info.value)
    assert "error is required when status is 'error'" in error_str


def test_summary_response_success_with_error_message_raises_error():
    """Test that success status with error message raises ValidationError."""
    summary = RepositorySummary()
    with pytest.raises(ValidationError) as exc_info:
        SummaryResponse(
            status="success",
            repository_summary=summary,
            error="Should not have error message",
        )
    
    error_str = str(exc_info.value)
    assert "error should be None when status is 'success'" in error_str


def test_summary_response_error_with_summary_allowed():
    """Test that error status can optionally have a repository_summary (partial results)."""
    summary = RepositorySummary()
    response = SummaryResponse(
        status="error",
        error="Error occurred after partial scan",
        repository_summary=summary,
    )
    assert response.status == "error"
    assert response.error == "Error occurred after partial scan"
    assert response.repository_summary == summary


def test_summary_response_defaults():
    """Test that default values work correctly for optional fields."""
    summary = RepositorySummary()
    # Success response - error should default to None
    response = SummaryResponse(
        status="success",
        repository_summary=summary,
    )
    assert response.error is None
    
    # Error response - repository_summary should default to None
    response = SummaryResponse(
        status="error",
        error="Error message",
    )
    assert response.repository_summary is None

