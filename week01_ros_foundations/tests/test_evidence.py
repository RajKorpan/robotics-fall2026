from __future__ import annotations

import unittest

from lab.evidence import evidence_id, graph_inventory


class EvidenceTests(unittest.TestCase):
    def test_identifier_is_stable_for_key_order(self) -> None:
        self.assertEqual(evidence_id({"a": 1, "b": 2}), evidence_id({"b": 2, "a": 1}))

    def test_graph_inventory_accepts_structured_entries(self) -> None:
        inventory = graph_inventory({
            "nodes": [{"name": "/node"}],
            "topics": [{"name": "/scan"}],
            "services": [{"name": "/reset_world"}],
        })
        self.assertEqual(inventory["nodes"], {"/node"})
        self.assertEqual(inventory["topics"], {"/scan"})
        self.assertEqual(inventory["services"], {"/reset_world"})


if __name__ == "__main__":
    unittest.main()
