import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import mock

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = spec_from_file_location("prepare_zenodo_bundle", SCRIPTS / "prepare_zenodo_bundle.py")
ZENODO = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ZENODO)
ORIGINAL_RESOLVE_REPOSITORY_STATE = ZENODO.resolve_repository_state
PUBLIC_TABLE_COLUMNS = {
    stem: tuple(columns)
    for stem, columns in json.loads(
        (ROOT / "schemas" / "public-table-columns.json").read_text(encoding="utf-8")
    ).items()
}


class ZenodoBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_state_patcher = mock.patch.object(
            ZENODO, "resolve_repository_state", return_value="a" * 40
        )
        self.repository_state = self.repository_state_patcher.start()

    def tearDown(self) -> None:
        self.repository_state_patcher.stop()

    def test_current_configured_beta_is_rejected_without_output(self) -> None:
        self.assertIn("-beta.", ZENODO.VERSION)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "should-not-exist.zip"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "prepare_zenodo_bundle.py"),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to prepare Zenodo bundle", result.stderr)
            self.assertFalse(output.exists())

    def test_published_beta_manifest_cannot_pass_stable_gate(self) -> None:
        beta_manifest = json.loads(
            (ROOT / "release" / "v0.1.0-beta.2" / "manifests" / "release.json").read_text(
                encoding="utf-8"
            )
        )
        with self.assertRaisesRegex(ZENODO.BundleError, "stable release gate is closed"):
            ZENODO.validate_stable_gate("v0.1.0-beta.2", beta_manifest)

    def test_stable_fixture_build_is_reproducible_and_self_contained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "atlas"
            version = "v1.0.0"
            release = root / "release" / version
            data = release / "data" / "core"
            manifests = release / "manifests"
            data.mkdir(parents=True)
            manifests.mkdir(parents=True)

            for relative in (
                *ZENODO.DOCUMENTATION_FILES,
                *ZENODO.GOVERNANCE_FILES,
                *ZENODO.LICENSE_FILES,
                *ZENODO.SUPPORT_FILES,
                *ZENODO.REPRODUCIBILITY_FILES,
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"fixture for {relative}\n", encoding="utf-8")
            for repository_relative in ZENODO.REPOSITORY_LEVEL_FILES.values():
                path = root.parent / repository_relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"fixture for repository file {repository_relative}\n",
                    encoding="utf-8",
                )

            signoff_roles = ("methods", "evidence", "legal", "independent", "release")

            def parquet_bytes(rows: list[dict[str, str]], columns: tuple[str, ...]) -> bytes:
                table = pa.table(
                    {
                        column: pa.array([row[column] for row in rows], type=pa.string())
                        for column in columns
                    }
                )
                sink = pa.BufferOutputStream()
                pq.write_table(table, sink)
                return sink.getvalue().to_pybytes()

            base_payloads: dict[str, bytes] = {}
            gate_stem = "data/core/stable_release_gates"
            preview_release = ROOT / "release" / ZENODO.VERSION
            for stem in PUBLIC_TABLE_COLUMNS:
                if stem == gate_stem:
                    continue
                base_payloads[f"{stem}.csv"] = (preview_release / f"{stem}.csv").read_bytes()
                base_payloads[f"{stem}.parquet"] = (
                    preview_release / f"{stem}.parquet"
                ).read_bytes()

            claim_rows = list(
                csv.DictReader(io.StringIO(base_payloads["data/core/claims.csv"].decode("utf-8")))
            )
            relation_stem = "data/relations/claim_sources"
            relation_columns = PUBLIC_TABLE_COLUMNS[relation_stem]
            relation_rows = list(
                csv.DictReader(io.StringIO(base_payloads[f"{relation_stem}.csv"].decode("utf-8")))
            )
            linked_claim_ids = {row["claim_id"] for row in relation_rows}
            for index, claim in enumerate(
                (row for row in claim_rows if row["claim_id"] not in linked_claim_ids),
                start=8000,
            ):
                relation_rows.append(
                    {
                        "relation_id": f"CS-{index:04d}",
                        "claim_id": claim["claim_id"],
                        "source_id": "SRC-001",
                        "support_relation": "Supports",
                        "basis_note": "Stable fixture disposition link",
                        "applicability_scope": "Fixture only",
                        "verification_level": "Claim checked — empirical source",
                        "notes": "Synthetic test fixture; not research data",
                        "merged_relation_ids": "",
                        "publication_relation_status": "claim_support_checked",
                    }
                )
            relation_buffer = io.StringIO(newline="")
            relation_writer = csv.DictWriter(
                relation_buffer, fieldnames=relation_columns, lineterminator="\n"
            )
            relation_writer.writeheader()
            relation_writer.writerows(relation_rows)
            base_payloads[f"{relation_stem}.csv"] = relation_buffer.getvalue().encode()
            base_payloads[f"{relation_stem}.parquet"] = parquet_bytes(
                relation_rows, relation_columns
            )
            base_file_metadata = {
                relative: {
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "bytes": len(content),
                }
                for relative, content in base_payloads.items()
            }
            data_subject = hashlib.sha256(
                json.dumps(
                    base_file_metadata,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            qa_report = {
                "artifact_version": "1.0.0",
                "release_data_subject_sha256": data_subject,
                "validator_sha256": ZENODO.sha256_file(root / "scripts" / "validate_release.py"),
                "environment_lock_sha256": ZENODO.sha256_file(root.parent / "uv.lock"),
                "errors": 0,
                "warnings": 0,
                "csv_parquet_semantic_parity": True,
                "two_clean_builds_byte_identical": True,
                "fresh_checkout_validation_passed": True,
                "hf_viewer_smoke_test_passed": True,
                "generated_at": "2026-08-15T00:00:00Z",
            }
            evidence_payloads = {
                f"review/gate-SR-{index:02d}.md": (
                    f"verified evidence for SR-{index:02d}\n"
                ).encode()
                for index in range(1, 14)
            }
            evidence_payloads.pop("review/gate-SR-09.md")
            evidence_payloads["review/stable-validation-report.json"] = (
                json.dumps(qa_report, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            gate_lines = [
                "gate_id,gate,requirement,status,evidence_path,evidence_sha256,"
                "blocking_reason,human_signoff_required,human_signoff_role"
            ]
            for index in range(1, 14):
                evidence_relative = (
                    "review/stable-validation-report.json"
                    if index == 9
                    else f"review/gate-SR-{index:02d}.md"
                )
                evidence_digest = hashlib.sha256(evidence_payloads[evidence_relative]).hexdigest()
                status = "ready_for_deposit" if index == 13 else "satisfied"
                role = signoff_roles[(index - 1) % len(signoff_roles)]
                gate_lines.append(
                    f"SR-{index:02d},Gate {index},Verified requirement {index},"
                    f"{status},{evidence_relative},{evidence_digest},,true,{role}"
                )
            gate_bytes = ("\n".join(gate_lines) + "\n").encode("utf-8")
            gate_rows = list(csv.DictReader(io.StringIO(gate_bytes.decode("utf-8"))))
            payloads = {
                **base_payloads,
                "data/core/stable_release_gates.csv": gate_bytes,
                "data/core/stable_release_gates.parquet": parquet_bytes(
                    gate_rows, PUBLIC_TABLE_COLUMNS[gate_stem]
                ),
            }
            for relative, content in payloads.items():
                path = release / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            manifest = {
                "artifact": "Agency Transfer Policy Atlas",
                "artifact_version": "1.0.0",
                "release_stage": "stable",
                "stable_release_ready": True,
                "stable_release_blockers": [],
                "formats": ["csv", "parquet"],
                "counts": {
                    "stable_release_gates": 13,
                    "stable_release_gates_blocked": 0,
                },
                "doi": {
                    "authority": "Zenodo",
                    "version_doi": "10.5281/zenodo.1234567",
                    "concept_doi": "10.5281/zenodo.1234500",
                    "concept_doi_status": "known_existing_concept",
                    "reservation_status": "reserved_not_deposited",
                },
                "files": {
                    relative: {
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "bytes": len(content),
                    }
                    for relative, content in payloads.items()
                },
            }
            count_contract = {
                "control_families": "data/core/intervention_families",
                "implementations": "data/core/implementations",
                "claims": "data/core/claims",
                "sources": "data/core/sources",
                "mechanisms": "data/core/mechanisms",
                "legal_instruments": "data/core/legal_instruments",
                "policy_packages": "data/core/policy_packages",
                "decision_gates": "data/core/decision_gates",
                "context_entities": "data/core/context_entities",
                "research_gaps": "data/core/research_gaps",
                "claim_source_edges_unique": "data/relations/claim_sources",
                "proposed_stable_core_candidates": "data/derived/stable_core_candidates",
                "candidate_registry_implementations": "data/derived/candidate_registry",
            }
            for key, stem in count_contract.items():
                manifest["counts"][key] = len(
                    list(csv.DictReader(io.StringIO(payloads[f"{stem}.csv"].decode("utf-8"))))
                )
            for relative, content in evidence_payloads.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            (root / "CITATION.cff").write_text(
                "cff-version: 1.2.0\n"
                'title: "Fixture"\n'
                'version: "1.0.0"\n'
                'date-released: "2026-08-15"\n'
                'url: "https://doi.org/10.5281/zenodo.1234567"\n'
                'doi: "10.5281/zenodo.1234567"\n',
                encoding="utf-8",
            )
            (root / "README.md").write_text(
                "Version DOI: 10.5281/zenodo.1234567\nConcept DOI: 10.5281/zenodo.1234500\n",
                encoding="utf-8",
            )
            (root / "review" / "stable_release_gates.csv").write_bytes(gate_bytes)

            preservation_files = {relative: release / relative for relative in payloads}
            for relative in (
                *ZENODO.DOCUMENTATION_FILES,
                *ZENODO.GOVERNANCE_FILES,
                *ZENODO.LICENSE_FILES,
                *ZENODO.SUPPORT_FILES,
                *ZENODO.REPRODUCIBILITY_FILES,
            ):
                preservation_files[relative] = root / relative
            for archive_relative, repository_relative in ZENODO.REPOSITORY_LEVEL_FILES.items():
                preservation_files[archive_relative] = root.parent / repository_relative
            for relative in evidence_payloads:
                preservation_files[relative] = root / relative

            review_subject = ZENODO.preservation_subject_sha256(preservation_files, manifest)
            manifest["human_review_signoffs"] = [
                {
                    "role": role,
                    "reviewer_id": f"reviewer-{role}",
                    "decision": "approved",
                    "signed_on": "2026-08-15",
                    "review_subject_sha256": review_subject,
                }
                for role in sorted(ZENODO.REQUIRED_SIGNOFF_ROLES)
            ]
            ZENODO.validate_human_signoffs(manifest)
            ZENODO.validate_signoff_subjects(manifest, preservation_files)
            changed_after_review = json.loads(json.dumps(manifest))
            changed_after_review["doi"]["version_doi"] = "10.5281/zenodo.7654321"
            with self.assertRaisesRegex(
                ZENODO.BundleError, "not bound to the preservation subject"
            ):
                ZENODO.validate_signoff_subjects(changed_after_review, preservation_files)
            manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
            (manifests / "release.json").write_bytes(manifest_bytes)
            checksums = [
                f"{hashlib.sha256(content).hexdigest()}  {relative}"
                for relative, content in sorted(payloads.items())
            ]
            checksums.append(
                f"{hashlib.sha256(manifest_bytes).hexdigest()}  manifests/release.json"
            )
            (manifests / "checksums.sha256").write_text(
                "\n".join(checksums) + "\n", encoding="utf-8"
            )

            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            first_digest = ZENODO.prepare_bundle(root, version, first)
            second_digest = ZENODO.prepare_bundle(root, version, second)
            self.assertGreaterEqual(self.repository_state.call_count, 2)
            self.assertEqual(first_digest, second_digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())

            archive_root = "agency-transfer-policy-atlas-v1.0.0"
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
                self.assertIn(f"{archive_root}/data/core/claims.csv", names)
                self.assertIn(f"{archive_root}/DOI_RELEASE.md", names)
                self.assertIn(f"{archive_root}/protocol/RANKING_PROTOCOL.md", names)
                self.assertIn(f"{archive_root}/GOVERNANCE.md", names)
                self.assertIn(f"{archive_root}/LICENSES/DATA.md", names)
                bundle_manifest = json.loads(archive.read(f"{archive_root}/BUNDLE-MANIFEST.json"))
                self.assertEqual(bundle_manifest["deposit_status"], "reserved_not_deposited")
                self.assertEqual(bundle_manifest["version_doi"], "10.5281/zenodo.1234567")
                self.assertEqual(bundle_manifest["concept_doi"], "10.5281/zenodo.1234500")
                self.assertEqual(bundle_manifest["repository_commit"], "a" * 40)

            leak = root / "scripts" / "build_release.py"
            original_leak_content = leak.read_bytes()
            leak.write_text("hf_" + "A" * 24 + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ZENODO.BundleError, "credential marker"):
                ZENODO.validate_bundle_safety(preservation_files)
            with self.assertRaisesRegex(
                ZENODO.BundleError, "not bound to the preservation subject"
            ):
                ZENODO.prepare_bundle(
                    root,
                    version,
                    Path(temporary) / "must-not-exist.zip",
                )
            leak.write_bytes(original_leak_content)

            unstable = root / "METHODS.md"
            original_read_bytes = Path.read_bytes

            def changed_during_zip(path: Path) -> bytes:
                if path == unstable:
                    return b"changed after bundle inventory\n"
                return original_read_bytes(path)

            with (
                mock.patch.object(Path, "read_bytes", changed_during_zip),
                self.assertRaisesRegex(ZENODO.BundleError, "differs from bundle manifest"),
            ):
                ZENODO.prepare_bundle(
                    root,
                    version,
                    Path(temporary) / "must-also-not-exist.zip",
                )

            table = release / "data" / "core" / "claims.csv"
            table.write_bytes(table.read_bytes() + b"tampered\n")
            with self.assertRaisesRegex(ZENODO.BundleError, "checksum mismatch"):
                ZENODO.validate_release_inventory(release, manifest)

    def test_stable_flags_without_substantive_gates_or_signoffs_are_rejected(self) -> None:
        manifest = {
            "artifact": "Agency Transfer Policy Atlas",
            "artifact_version": "1.0.0",
            "release_stage": "stable",
            "repository_commit": "a" * 40,
            "stable_release_ready": True,
            "stable_release_blockers": [],
            "formats": ["csv", "parquet"],
            "counts": {"stable_release_gates": 13, "stable_release_gates_blocked": 0},
        }
        with self.assertRaisesRegex(ZENODO.BundleError, "human review sign-offs"):
            ZENODO.validate_stable_gate("v1.0.0", manifest)
        with self.assertRaisesRegex(ZENODO.BundleError, "final SemVer"):
            ZENODO.validate_stable_gate("v0.2.0", manifest)

    def test_repository_commit_must_match_clean_tagged_head(self) -> None:
        root = Path("/tmp/example/policy-atlas")
        with (
            mock.patch.object(
                ZENODO, "git_output", side_effect=["/tmp/example", "a" * 40, "b" * 40]
            ),
            self.assertRaisesRegex(ZENODO.BundleError, "does not point"),
        ):
            ORIGINAL_RESOLVE_REPOSITORY_STATE(root, "v1.0.0")

    def test_credential_scan_covers_common_token_families(self) -> None:
        candidates = (
            "hf_" + "A" * 24,
            "ghp_" + "A" * 36,
            "github_pat_" + "A" * 40,
            "AKIA" + "A" * 16,
            "xoxb-" + "A" * 24,
            "AIza" + "A" * 35,
            "npm_" + "A" * 36,
            "sk_live_" + "A" * 24,
        )
        for candidate in candidates:
            with self.subTest(candidate=candidate[:8]):
                self.assertIsNotNone(ZENODO.CREDENTIAL_PATTERN.search(candidate))
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / "metadata.parquet"
            binary.write_bytes(b"PAR1\xff\x00publisher_secret=hf_" + b"A" * 24 + b"\x00PAR1")
            with self.assertRaisesRegex(ZENODO.BundleError, "credential marker"):
                ZENODO.validate_bundle_safety({"data/core/claims.parquet": binary})


if __name__ == "__main__":
    unittest.main()
