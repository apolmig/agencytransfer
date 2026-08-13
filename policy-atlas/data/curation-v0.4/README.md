# Curation v0.4 — evidence wave 1

This overlay records claim-specific corrections made after reading primary
legal or empirical sources. It is applied to, but never rewrites, the frozen
`data/draft-v0.3` Sheets snapshot.

Blank cells in a correction file mean “leave the base value unchanged.” Every
material replacement, including a deliberate removal, must be expressed
explicitly rather than inferred from an empty cell. Additions use stable IDs
that are never renumbered.

Wave 1 contains:

- six corrected control-effect claims and their six implementation-level
  classifications, plus two corrected legal-scope claims;
- two corrected empirical source records and four new empirical sources;
- five corrected legal-instrument records and five new official sources;
- seven new checked claim–source relations plus three corrected relations;
- three implementation-level legal-scope corrections; and
- a structured review recording design, sample, endpoint, and limitation for
  every priority effect claim.

The release builder applies corrections by primary key, rejects corrections to
unknown IDs or fields, and validates additions for uniqueness and referential
integrity before publication.
