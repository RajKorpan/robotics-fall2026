import unittest

from course_evidence_collector.collector import graph_snapshot_payload


class GraphSnapshotTests(unittest.TestCase):
    def test_snapshot_includes_sorted_services_and_schema_version(self):
        payload = graph_snapshot_payload(
            nodes=[{"name": "/z_node"}, {"name": "/a_node"}],
            topics=[{"name": "/scan", "types": ["sensor_msgs/msg/LaserScan"]}],
            services=[
                {"name": "/z_service", "types": ["std_srvs/srv/Empty"]},
                {"name": "/a_service", "types": ["std_srvs/srv/Empty"]},
            ],
            samples={"/scan": None},
            captured_at="2026-09-01T00:00:00Z",
        )
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual([item["name"] for item in payload["nodes"]], ["/a_node", "/z_node"])
        self.assertEqual([item["name"] for item in payload["services"]], ["/a_service", "/z_service"])
        self.assertEqual(payload["captured_at"], "2026-09-01T00:00:00Z")
