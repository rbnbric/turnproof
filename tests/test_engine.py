import tempfile
import unittest
from pathlib import Path

from server.engine import DiagnosisEngine, DiagnosisError


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = DiagnosisEngine(Path(self.temp.name) / "test.db")

    def tearDown(self):
        self.temp.cleanup()

    def test_evidence_changes_ranking_and_persists(self):
        opened = self.engine.open_incident("dehumidifier", "It runs but collects no water")
        incident_id = opened["incident_id"]
        self.assertEqual(opened["next_check"]["id"], "bucket_light")
        updated = self.engine.record_observation(incident_id, "bucket_light", "yes")
        self.assertEqual(updated["ranked_causes"][0]["id"], "bucket")
        reopened = DiagnosisEngine(Path(self.temp.name) / "test.db")
        self.assertEqual(reopened.summary(incident_id)["observations"], {"bucket_light": "yes"})

    def test_same_evidence_has_same_ranking(self):
        first = self.engine.open_incident("washer", "It bangs during spin")
        second = self.engine.open_incident("washer", "It bangs during spin")
        for item in (first, second):
            self.engine.record_observation(item["incident_id"], "single_item", "no")
            self.engine.record_observation(item["incident_id"], "rocks", "yes")
        self.assertEqual(
            self.engine.summary(first["incident_id"])["ranked_causes"],
            self.engine.summary(second["incident_id"])["ranked_causes"],
        )

    def test_next_check_has_positive_expected_information_gain(self):
        opened = self.engine.open_incident("dehumidifier", "It runs but collects no water")
        check = opened["next_check"]
        self.assertEqual(check["id"], "bucket_light")
        self.assertGreater(check["information_gain_bits"], 0)

    def test_hazard_stops_diagnosis(self):
        opened = self.engine.open_incident("dehumidifier", "There is smoke and a burning smell")
        self.assertEqual(opened["status"], "safety_stop")
        self.assertIsNone(opened["next_check"])
        self.assertIn("Stop using", opened["safety_message"])
        with self.assertRaises(DiagnosisError):
            self.engine.record_observation(opened["incident_id"], "bucket_light", "yes")

    def test_resolution_requires_evidence_and_verification(self):
        opened = self.engine.open_incident("washer", "It bangs")
        with self.assertRaises(DiagnosisError):
            self.engine.propose_resolution(opened["incident_id"])
        self.engine.record_observation(opened["incident_id"], "single_item", "yes")
        proposed = self.engine.propose_resolution(opened["incident_id"])
        self.assertTrue(proposed["requires_verification"])
        closed = self.engine.verify_resolution(opened["incident_id"], True)
        self.assertEqual(closed["status"], "resolved")
        self.assertTrue(closed["verified"])

    def test_rejects_unknown_inputs(self):
        with self.assertRaises(DiagnosisError):
            self.engine.open_incident("furnace", "no heat")
        opened = self.engine.open_incident("washer", "It bangs")
        with self.assertRaises(DiagnosisError):
            self.engine.record_observation(opened["incident_id"], "made_up", "yes")


if __name__ == "__main__":
    unittest.main()
