import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from server.engine import DiagnosisEngine
from server.mcp import PROTOCOL_VERSION
from server.semantic import SemanticEngine
import server.app as application


class McpTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        application.engine = DiagnosisEngine(Path(self.temp.name) / "mcp.db")
        application.semantic = SemanticEngine(Path(self.temp.name) / "mcp.db")
        application.sessions.clear()
        self.client = TestClient(application.app)
        self.accept = {"Accept": "application/json, text/event-stream"}

    def tearDown(self):
        self.temp.cleanup()

    def initialize(self):
        response = self.client.post("/mcp", headers=self.accept, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                       "clientInfo": {"name": "test", "version": "1"}},
        })
        self.assertEqual(response.status_code, 200)
        return response.headers["mcp-session-id"]

    def test_initialize_and_list_tools(self):
        session = self.initialize()
        response = self.client.post("/mcp", headers={**self.accept,
            "MCP-Session-Id": session, "MCP-Protocol-Version": PROTOCOL_VERSION}, json={
                "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}
            })
        self.assertEqual(response.status_code, 200)
        names = [tool["name"] for tool in response.json()["result"]["tools"]]
        self.assertIn("open_incident", names)
        self.assertIn("verify_resolution", names)
        self.assertIn("start_turnproof_diagnosis", names)
        self.assertIn("commit_turnproof_action", names)

    def test_turnproof_revision_flow_over_real_mcp_dispatch(self):
        session = self.initialize()
        headers = {**self.accept, "MCP-Session-Id": session, "MCP-Protocol-Version": PROTOCOL_VERSION}

        def call(request_id, name, arguments):
            response = self.client.post("/mcp", headers=headers, json={
                "jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            })
            self.assertEqual(response.status_code, 200)
            return response.json()["result"]

        opened = call(2, "start_turnproof_diagnosis", {
            "scenario": "dehumidifier", "symptom": "bucket stays dry",
        })["structuredContent"]
        first = call(3, "revise_turnproof_fact", {
            "conversation_id": opened["conversation_id"], "expected_revision": opened["revision"],
            "idempotency_key": "answer-1", "field": "bucket_light", "operation": "set", "value": "no",
        })["structuredContent"]
        corrected = call(4, "revise_turnproof_fact", {
            "conversation_id": opened["conversation_id"], "expected_revision": first["revision"],
            "idempotency_key": "answer-2", "field": "bucket_light", "operation": "set", "value": "yes",
        })["structuredContent"]
        self.assertEqual(corrected["changed"][0]["operation"], "replace")
        self.assertEqual(corrected["understood"]["bucket_light"], "yes")

    def test_generated_lab_is_exposed(self):
        response = self.client.get("/api/turnproof/lab")
        self.assertEqual(response.status_code, 200)
        report = response.json()
        self.assertEqual(report["passed"], report["total"])
        self.assertEqual(len(report["contracts"]), 2)

    def test_observatory_history_uses_semantic_ledger(self):
        opened = application.semantic.open_conversation("household_handoff_v1", {
            "recipient": "Sam", "task": "pick up prescription", "time_window": "after work",
        })
        response = self.client.get(f"/api/turnproof/conversations/{opened['conversation_id']}/history")
        self.assertEqual(response.status_code, 200)
        events = response.json()["events"]
        self.assertEqual({event["field"] for event in events}, {"recipient", "task", "time_window"})

    def test_session_and_version_are_enforced(self):
        response = self.client.post("/mcp", headers=self.accept, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        self.assertEqual(response.status_code, 400)
        session = self.initialize()
        response = self.client.post("/mcp", headers={**self.accept,
            "MCP-Session-Id": session, "MCP-Protocol-Version": "2025-03-26"}, json={
                "jsonrpc": "2.0", "id": 3, "method": "ping"})
        self.assertEqual(response.status_code, 400)

    def test_origin_is_validated(self):
        response = self.client.post("/mcp", headers={**self.accept, "Origin": "https://attacker.invalid"}, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION}})
        self.assertEqual(response.status_code, 403)

    def test_local_origin_is_allowed_on_any_port(self):
        response = self.client.post("/mcp", headers={**self.accept, "Origin": "http://127.0.0.1:8765"}, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION}})
        self.assertEqual(response.status_code, 200)

    def test_notification_and_session_delete(self):
        session = self.initialize()
        headers = {**self.accept, "MCP-Session-Id": session, "MCP-Protocol-Version": PROTOCOL_VERSION}
        response = self.client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(self.client.delete("/mcp", headers=headers).status_code, 204)
        self.assertEqual(self.client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 4, "method": "ping"}).status_code, 404)

    def test_get_explicitly_declines_server_stream(self):
        session = self.initialize()
        response = self.client.get("/mcp", headers={
            "Accept": "text/event-stream", "MCP-Session-Id": session,
            "MCP-Protocol-Version": PROTOCOL_VERSION})
        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
