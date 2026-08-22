# DOI and preservation release policy

The Agency Transfer Policy Atlas does **not** currently have a DOI. The beta
and research-preview releases are not eligible for one. A DOI is a durable
citation commitment, not a substitute for evidence review or a way to make a
preview look stable.

## One DOI authority

Zenodo is the sole DOI authority for stable Policy Atlas dataset releases.
Hugging Face remains a distribution and exploration mirror and must not mint a
second DOI for the same dataset. Once a stable version DOI exists, the matching
Hugging Face release may link to it, but it must not describe itself as the
archival copy.

This separation gives each service one clear role:

- **Zenodo:** immutable preservation record and DOI-bearing archive;
- **Hugging Face:** convenient table viewer and versioned distribution mirror;
- **GitHub:** source, methods, review history, issues, and release engineering.

## Version DOI and concept DOI

Zenodo assigns two identifiers with different citation semantics:

- the **version DOI** identifies one exact, immutable stable dataset release;
- the **concept DOI** identifies the evolving dataset across its Zenodo
  versions and normally resolves to the latest deposited version.

Reproducible analysis must cite the version DOI. The concept DOI is appropriate
only when referring to the Policy Atlas as a continuing project rather than to
the exact records used in an analysis. A later release must receive a new
version DOI under the same Zenodo concept record; it must not replace files in
an already published deposition.

No DOI or ORCID may be guessed, reserved in prose, or copied from a different
artifact. Record identifiers only after Zenodo has actually issued them.

## Eligibility gates

A Zenodo bundle may be prepared only when all of the following are true:

1. `scripts/release_config.py` selects a final SemVer version such as `v1.0.0`,
   with no beta or other prerelease suffix;
2. the selected release manifest says `release_stage: stable`;
3. the manifest says `stable_release_ready: true` and has no stable-release
   blockers;
4. the manifest inventory, byte counts, and SHA-256 checksums match the release
   directory exactly;
5. the required documentation, protocols, governance files, review materials,
   schemas, frozen source snapshot, curation overlays, release code, tests,
   dependency locks, and data/code licences are present;
6. the human-review and authorship records contain only real, documented
   contributors. The bundling script does not infer or fabricate reviewers,
   ORCIDs, or approvals;
7. SR-01 through SR-12 are `satisfied`, SR-13 is
   `ready_for_deposit`, and every gate cites a bundled evidence file by exact
   SHA-256 and the required human sign-off role; and
8. a real Zenodo version DOI has been reserved and recorded in the stable
   manifest, `CITATION.cff`, and `README.md`; an existing concept DOI is also
   recorded, or the first deposition explicitly records that its concept DOI
   remains pending publication; and
9. every preservation input is committed, the relevant Git tree is clean,
   and the final version tag points to that exact commit. The generated
   `BUNDLE-MANIFEST.json` pins that full SHA; it is generated after the tag to
   avoid a self-referential commit hash.

The local bundler is intentionally fail-closed. Run it from the repository
root with:

```bash
python policy-atlas/scripts/prepare_zenodo_bundle.py
```

It produces a deterministic, uncompressed ZIP under `policy-atlas/dist/zenodo/`
only after the gates pass. The ZIP contains the exact release and checksums
plus its frozen source data, curation overlays, build and validation code,
tests, dependency locks, documentation, protocols, governance and correction
procedures, schemas, hashed gate evidence, review material, and licences. It
also contains a generated `BUNDLE-MANIFEST.json` covering every bundled file
and pinning the repository commit and reserved DOI pair.

SR-09 must cite a bundled machine-readable QA report linked to the released
data inventory, validator, and environment lock. The bundler also opens every
Parquet file, compares its typed cell semantics with the matching CSV, checks
non-empty/partition/count invariants, and requires complete claim relations; a
declarative report alone cannot satisfy these checks. Every human sign-off
must carry the digest of the full preservation subject—data, manifest subject,
methods, protocols, sources, code, dependency locks, licences, review evidence,
and documentation—so changing any of those inputs invalidates the approvals.

The script has no network code, does not read a Zenodo token, does not create a
deposition, and does not mint or reserve a DOI.

## Manual Zenodo publication procedure

After SR-01 through SR-12 and the human reviews have passed:

1. In Zenodo, manually create a new version under the existing Policy Atlas
   concept record, or create the first record if none exists.
2. Enter only verified title, authors, affiliations, ORCIDs, licence, funding,
   and related identifiers. Do not list a reviewer as an author by default.
3. Reserve the version DOI in the unpublished draft. For a new version under
   an existing record, copy the existing concept DOI. For a first deposition,
   record `concept_doi_status=pending_first_publication` and leave the concept
   DOI null: Zenodo registers the concept DOI when the first upload is
   published. Never derive or guess either identifier.
4. Add the real version DOI and concept status to the frozen stable manifest
   and README, add the version DOI to the structured `doi` field in
   `CITATION.cff`, bind each sign-off to the reviewed preservation-subject
   digest, and set SR-13 to `ready_for_deposit` with hashed evidence.
5. Commit the reviewed stable candidate, verify the relevant tree is clean,
   and create the final version tag at that exact commit. The tag and `HEAD`
   must resolve to the same full SHA; the bundler records it in its generated
   manifest.
6. Run the bundler and record the ZIP's SHA-256 digest in the release review.
   The bundler refuses a missing DOI, missing sign-off, unhashed gate evidence,
   incomplete reproducibility inventory, dirty preservation input, or
   mismatched tag/commit.
7. Have a maintainer and independent reviewer inspect the ZIP inventory and
   compare the embedded release manifest with the approved stable release.
8. Upload that exact reviewed ZIP to the existing Zenodo draft. Do not rebuild
   it after approval without repeating the checksum and review process.
9. Publish manually, then verify that downloading the Zenodo file reproduces
   the approved ZIP digest. Point the matching Hugging Face version to the
   version DOI; do not mint a second DOI there.

If any metadata, file, checksum, or gate changes after a draft is prepared,
discard the draft bundle and repeat the review. Policy Atlas treats every
published Zenodo version as immutable even if the platform offers a limited
file-correction window. Corrections require a documented new version or, for a
serious integrity issue, Zenodo's withdrawal process plus the repository
correction record.

## Official platform references

- Zenodo DOI reservation: https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/
- Zenodo version and concept DOIs: https://zenodo.org/help/versioning
- Hugging Face DOI persistence constraints: https://huggingface.co/docs/hub/doi
- OSF prospective registrations: https://help.osf.io/article/330-welcome-to-registrations

OSF is used only for prospective registration of the ranking protocol. It is
not the canonical workspace or the DOI archive for the Policy Atlas dataset.
