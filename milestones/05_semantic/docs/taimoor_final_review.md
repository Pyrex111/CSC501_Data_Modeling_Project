# Taimoor: report query and backend review

Reviewed against report PR #2, head `12ccab6a1c9e982a8f446ac4f5fe36e8e7d4ca76`.
AI prepared the report edits and executed the checks recorded here. This record
does not claim that Taimoor personally executed them or that the team approved
the final submission.

## Contribution delivered

- Revised `report/taimoor_semantic_section.tex` includes an actual SELECT and its
  five result rows, rather than only reporting query counts.
- `report/examples/taimoor_snapshot_totals.sparql` is a standalone executable query
  with prefix declarations. The report displays it using `lstinputlisting`, so
  the code shown and the code executed come from the same file.
- `taimoor_query_evidence.json` records the query SHA-256, exact results, SQL
  comparison, graph sizes and the six complete-result parity comparisons.

The query is a reduced projection of Q3: `(id, n, total)` per snapshot, sorted by
ID. The observed results are `(1,3,1.0)`, `(2,5,1.0)`, `(3,2,1.0)`,
`(4,3,1.0)` and `(5,4,1.0)`. All five seeded snapshots are Complete. The result
accounts for 17 allocation entries and excludes the five portfolio holdings.
The SELECT itself does not enforce totals; validation applies the documented
prototype tolerance only to Complete snapshots.

## Backend claims checked

| Statement | Evidence / conclusion |
| --- | --- |
| Record IRIs | `vocabulary.resource()` emits `resource/{Table}/{Id}`. Business keys are separate; these are not business-key URI templates or permanent external identities. |
| Population | A fresh accepted seed exports 356 ABox triples; integrated startup loads 504 ontology triples into a different named graph. |
| Query correctness | The displayed query matches the independently executed SQL Q3 projection; all six full SQL/SPARQL result multisets match. SELECT leaves the quad set unchanged. |
| Shared `weightFraction` | The query explicitly requires `AllocationEntry`; weights on `Holding` are excluded. |
| Validation | `runtime.open_graph_database()` binds the native validator and capture root. `GraphDatabase.validate()` first runs the M4 parity bridge, then the native callback. |
| Atomic writes | A candidate is validated before one live SPARQL delta; repository operations preserve the live graph after rejected writes. Nine runtime tests isolate native checks where needed. |
| OWL behavior | The store retains ontology axioms but enables no reasoner. Write checks read only the data named graph; no query-time FIBO inference is claimed. |
| Unknown classification editions | A second unknown-version scheme with the same authority/name is accepted by the integrated backend. It is not automatically equivalent to the existing scheme. |
| `--serve` | Independently launched on a temporary store during PR review; search/detail HTTP requests succeed and all six comparisons match. The existing graph is passed to Flask; no second writable instance is opened. |
| Full application suite | 189 tests passed during review of the unchanged application/backend baseline. This contribution changes report/evidence files only and adds no tests. |

## Package review and remaining assembly work

The original PR-head PDF has exactly three pages. Its ZIP is valid, the original
report source/PDF matched its repository counterparts, and all eleven screenshot
images matched their repository originals. Those were checks of the baseline
package, before this contribution's source changes.

The final package is **not yet approved**. Mason still needs to:

1. Correct the ontology section's business-key IRI claim, unknown-version rejection
   claim, and overly broad assertions about OWL keys and closed literal sets.
2. Integrate Shahmeer's larger/simpler architecture figure and correct its source
   path. The repository figure is in `../figures/`; the original ZIP also has its
   own `figures/` directory.
3. Make AI attribution consistent with Shahmeer's Claude contribution record and
   obtain actual author review of the final prose.
4. Include the new `examples/taimoor_snapshot_totals.sparql` file in the source ZIP,
   regenerate `main.pdf` and the ZIP, and check the three-page length and readability.
5. Compare the regenerated source/PDF against the ZIP and repeat final package
   verification before merging PR #2.

The current tracked `main.pdf` and submission ZIP were deliberately not replaced
with an incomplete team revision. A local preview build was attempted in a staged
copy, with the figure present. `pdflatex` lacks its format file in this runtime;
Tectonic also could not build because its default resource bundle is unavailable
(HTTP 403). Consequently the revised report's page count and visual layout are
not verified here. Final compilation remains with the report assembler.

No application behavior, seed values, ontology axioms, six canonical SPARQL files,
or other members' report sections are changed by this contribution.
