import tempfile
import unittest
from pathlib import Path

from server.contracts import (
    DIAGNOSIS_CONTRACT,
    HANDOFF_CONTRACT,
    ContractError,
    compile_contract,
)
from server.lab import run_contract_lab
from server.semantic import SemanticEngine, SemanticError


class ContractTests(unittest.TestCase):
    def test_rejects_unknown_dependency(self):
        with self.assertRaises(ContractError):
            compile_contract({
                "id": "bad", "title": "Bad",
                "fields": {"answer": {"type": "string", "depends_on": ["missing"]}},
            })

    def test_rejects_dependency_cycle(self):
        with self.assertRaises(ContractError):
            compile_contract({
                "id": "cycle", "title": "Cycle",
                "fields": {
                    "a": {"type": "string", "depends_on": ["b"]},
                    "b": {"type": "string", "depends_on": ["a"]},
                },
            })


class SemanticEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "semantic.db"
        self.engine = SemanticEngine(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_revision_history_and_resume(self):
        opened = self.engine.open_conversation(DIAGNOSIS_CONTRACT.contract_id, {
            "scenario": "dehumidifier", "symptom": "bucket stays dry",
        })
        first = self.engine.apply_changes(
            opened["conversation_id"], [{"field": "bucket_light", "operation": "set", "value": "no"}],
            expected_revision=opened["revision"], idempotency_key="answer",
        )
        corrected = self.engine.apply_changes(
            opened["conversation_id"], [{"field": "bucket_light", "operation": "set", "value": "yes"}],
            expected_revision=first["revision"], idempotency_key="correct",
        )
        resumed = SemanticEngine(self.path).review(opened["conversation_id"])
        self.assertEqual(resumed["understood"]["bucket_light"], "yes")
        self.assertEqual(resumed["revision"], corrected["revision"])
        history = self.engine.history(opened["conversation_id"])
        self.assertEqual([item["operation"] for item in history if item["field"] == "bucket_light"], ["add", "replace"])

    def test_failed_batch_is_atomic(self):
        opened = self.engine.open_conversation(DIAGNOSIS_CONTRACT.contract_id)
        with self.assertRaises(SemanticError) as raised:
            self.engine.apply_changes(opened["conversation_id"], [
                {"field": "scenario", "operation": "set", "value": "washer"},
                {"field": "bucket_light", "operation": "set", "value": "maybe"},
            ], expected_revision=0, idempotency_key="bad-batch")
        self.assertEqual(raised.exception.code, "INVALID_VALUE")
        self.assertEqual(self.engine.review(opened["conversation_id"])["revision"], 0)

    def test_action_binds_to_exact_state(self):
        current = self.engine.open_conversation(DIAGNOSIS_CONTRACT.contract_id, {
            "scenario": "dehumidifier", "symptom": "dry bucket", "bucket_light": "no",
        })
        proposal = self.engine.propose(current["conversation_id"], "accept_resolution")
        changed = self.engine.apply_changes(
            current["conversation_id"], [{"field": "bucket_light", "operation": "set", "value": "yes"}],
            expected_revision=current["revision"], idempotency_key="correction",
        )
        self.assertEqual(changed["understood"]["bucket_light"], "yes")
        with self.assertRaises(SemanticError) as raised:
            self.engine.commit(proposal["proposal_id"], idempotency_key="commit")
        self.assertEqual(raised.exception.code, "STATE_CHANGED")

    def test_commit_retry_returns_identical_receipt(self):
        current = self.engine.open_conversation(HANDOFF_CONTRACT.contract_id, {
            "recipient": "Jordan", "task": "pick up prescription", "time_window": "after work",
        })
        proposal = self.engine.propose(current["conversation_id"], "send_handoff")
        first = self.engine.commit(proposal["proposal_id"], idempotency_key="delivery")
        second = self.engine.commit(proposal["proposal_id"], idempotency_key="delivery")
        self.assertEqual(first, second)

    def test_idempotency_key_cannot_hide_different_mutation(self):
        current = self.engine.open_conversation(DIAGNOSIS_CONTRACT.contract_id)
        first = self.engine.apply_changes(
            current["conversation_id"], [{"field": "scenario", "operation": "set", "value": "washer"}],
            expected_revision=0, idempotency_key="same-key",
        )
        with self.assertRaises(SemanticError) as raised:
            self.engine.apply_changes(
                current["conversation_id"], [{"field": "scenario", "operation": "set", "value": "dehumidifier"}],
                expected_revision=0, idempotency_key="same-key",
            )
        self.assertEqual(raised.exception.code, "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.engine.review(current["conversation_id"])["revision"], first["revision"])

    def test_idempotency_key_cannot_commit_another_proposal(self):
        current = self.engine.open_conversation(HANDOFF_CONTRACT.contract_id, {
            "recipient": "Jordan", "task": "pick up prescription", "time_window": "after work",
        })
        first = self.engine.propose(current["conversation_id"], "send_handoff")
        second = self.engine.propose(current["conversation_id"], "send_handoff")
        self.engine.commit(first["proposal_id"], idempotency_key="one-effect")
        with self.assertRaises(SemanticError) as raised:
            self.engine.commit(second["proposal_id"], idempotency_key="one-effect")
        self.assertEqual(raised.exception.code, "IDEMPOTENCY_CONFLICT")


class GeneratedLabTests(unittest.TestCase):
    def test_both_contracts_pass_generated_adversarial_checks(self):
        for contract in (DIAGNOSIS_CONTRACT, HANDOFF_CONTRACT):
            with self.subTest(contract=contract.contract_id):
                report = run_contract_lab(contract)
                self.assertEqual(report["passed"], report["total"], report)
                self.assertGreaterEqual(report["total"], 7)


if __name__ == "__main__":
    unittest.main()
