"""Enterprise compliance tests for Phoenix-RCA evidence masking.

This suite audits sensitive infrastructure evidence before it reaches an LLM
layer. The tests verify that regulated identifiers and credential-bearing
strings are replaced with approved redaction markers.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.log_parser import mask_sensitive_data


class TestDataMaskingCompliance(unittest.TestCase):
    """Validate enterprise evidence masking controls before LLM analysis."""

    def test_ipv4_masking(self) -> None:
        """IPv4 addresses must be replaced with the approved redaction marker."""

        masked_text = mask_sensitive_data("Database node responded from 192.168.1.55")

        self.assertIn("[REDACTED_IP]", masked_text)
        self.assertNotIn("192.168.1.55", masked_text)

    def test_credential_masking(self) -> None:
        """Database credential strings must be removed before model analysis."""

        masked_text = mask_sensitive_data(
            "Connection failed for postgres://user:pass@localhost/db"
        )

        self.assertIn("[REDACTED_CREDENTIAL]", masked_text)
        self.assertNotIn("postgres://user:pass@localhost/db", masked_text)


if __name__ == "__main__":
    unittest.main()
