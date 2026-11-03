# Taimoor's design evaluation: Milestone 4

Evaluation supplied: 3 November 2026. Baseline repository commit: `56a4bbe6671ec489ac03c0b976c5fcfe06a144d6`.

## Attribution and scope

Taimoor supplied the following six design decisions and rationales in the project conversation. This record preserves those decisions and distinguishes them from the assistant's code comparison and automated test rerun. It does not claim that Taimoor personally executed the tests or verified real provider documents.

Scope: identification, dated observations, captured-source identity, classification contexts, category identity and the complete-total tolerance. This is a design evaluation of the current schema/validator. It is not acceptance testing of the complete UI, every repository query, the final report package or genuine allocation observations.

## Evaluation supplied by Taimoor

| Area | Evaluation | Why it fits the project |
| --- | --- | --- |
| Identification rules | Retain the documented rules | They distinguish records using meaningful business identifiers and scope. Customer numbers identify bank customers, portfolio references are customer-specific, and ticker identity includes the exchange. Names remain descriptive. |
| Dated holdings and disclosures | Retain their separate identities and dates | A customer's position and a provider's published allocation are different observations. Separating them prevents a newer disclosure from silently replacing the allocation applicable to an earlier comparison. |
| Source identification | Retain URL plus retrieval timestamp | Provider webpages change. Identifying a retained capture supports reproducibility and allows different historical versions of the same URL. |
| Classification context | Retain verified scheme contexts and disclosure-local contexts for unresolved classifications | The project specifically addresses the ambiguity of allocation percentages. Preserving classification authority, edition and source context prevents matching labels from being treated automatically as equivalent categories. |
| Category identification | Retain dimension + context + label, with an explicit assumption | This is sufficient when labels are unique within their context. Duplicate labels with different meanings would require revising the rule. Residual categories such as “Other” need particular care. |
| Complete-total tolerance | Retain `0.005` provisionally | Allowing totals from 99.5% to 100.5% accommodates small discrepancies in rounded published percentages. It is configurable and applies only to Complete disclosures. The precise threshold still needs justification from genuine source precision. |

## What these conclusions were compared against

The assistant compared the supplied decisions with the following current implementation evidence:

| Evaluation area | Implementation evidence | Result / condition |
| --- | --- | --- |
| Identification | `schema.sql`: CustomerNumber uniqueness; (CustomerId, PortfolioReference); provider registration within jurisdiction; conditional ISIN and exchange-scoped ticker indexes | Consistent with retaining scoped business identity. Names/email remain descriptive. This accepts the rules, not the authenticity of every seeded identifier. |
| Dated observations | Holding uniqueness includes HoldingAsOfDate; snapshot uniqueness includes AllocationAsOfDate and source/block identity | Supports separate historical records. Query/UI date selection remains necessary; separate columns alone do not guarantee correct temporal comparisons. |
| Captured sources | SourceDocument UNIQUE(Url, RetrievedAt), canonical UTC capture timestamp and CapturedFileRef; file-existence check when capture_root is supplied | Supports capture identity and retrieval of retained evidence. The retained file must remain unchanged; URL/time and file existence do not prove content authenticity or immutability. |
| Classification context | ClassificationScheme known-version partial uniqueness; `scheme_context`, `disclosure_context` and per-entry context validation | Consistent with retaining known-edition and disclosure-local contexts. Matching tokens validate stored context consistency; evidence is still needed to call an edition verified. |
| Category identity | UNIQUE(AllocationDimensionId, ContextKey, Label), optional Code and ClassificationSchemeId | Consistent under the explicit one-label-per-context assumption. “Other” must not be shared across disclosures merely because it has the same label. |
| Complete totals | DEFAULT_TOTAL_TOLERANCE = 0.005; validation applies to Complete snapshots; boundary/configuration/rollback tests | Implementation matches the provisional decision. The numeric threshold is not yet calibrated using genuine source precision. |

## Clarifications retained with the evaluation

1. **Temporal behavior.** Separate dates preserve the observations needed for a correct historical query. The application must explicitly choose the holding date and disclosure date or an explained as-of policy. It must not silently select the latest disclosure for an earlier comparison. This evaluation accepts the data model; it does not assert that every current query already follows that policy.
2. **Meaning and evidence.** A known-version context is appropriate only when the authority/name/version and category meaning are supported by evidence. A string token is not evidence by itself. Unknown schemes or editions use disclosure-local contexts.
3. **Residual categories.** Even a known classification edition does not automatically define a provider's “Other” residual. Reuse a category only if its meaning is supported as the same. Otherwise give the residual a truthful disclosure-local context, or revise the category identity rule if duplicate labels occur within one context. Do not invent an edition or alter the recorded classification merely to pass validation.
4. **Source retention.** Keep the captured file associated with its retrieval record. If stronger evidence of unchanged content is required later, content hashing is a possible extension; it is not currently implemented or asserted.
5. **Evaluation versus execution.** The supplied table records design judgments. The assistant reran the current schema test suite on 3 November: 33 tests passed. Those tests use synthetic fixtures and do not establish genuine-source accuracy, query/UI correctness or final submission compliance.

## How to substantiate the provisional tolerance

The current default is a fraction of 0.005, equal to 0.5 percentage points. It accepts complete totals from 0.995 to 1.005 inclusive, with the validator's tiny floating-point comparison allowance. It does not mean a 0.005% tolerance.

For an exhaustive, non-overlapping allocation with n entries, each independently rounded to the nearest p percentage points, the conservative accumulated rounding bound is:

`fraction tolerance = n * p / 200`

For example, ten entries rounded to the nearest 0.1 percentage point give a bound of 0.005. Ten entries rounded to the nearest 0.01 percentage point give a bound of 0.0005. These are mathematical illustrations under the stated assumptions, not measurements of the team's provider sources.

Before presenting 0.005 as source-justified, inspect a genuine retained allocation block, record its category count and displayed precision/rounding convention, check that it is complete and non-overlapping, and compare the resulting bound with the policy. Missing categories, incompatible bases or overlapping classifications cannot be justified simply by increasing the tolerance.

Mason's contribution notes at the baseline commit identify the demo weights as synthetic and the retained source files as placeholders. Consequently this evaluation makes no claim of genuine-source calibration. For a clearly labeled synthetic demonstration, retain 0.005 as a provisional configurable policy and disclose that limitation. If real observations are used, either justify the policy from them or revise it consistently in code, tests and report text.

## Decision and remaining scope

- Retain the identification, observation-date, source-capture and context structure.
- Retain category uniqueness subject to the stated label/context and residual-category conditions.
- Retain 0.005 provisionally, without presenting it as an empirically verified provider tolerance.
- No schema or validator behavior is changed by this evaluation record.
- Review the integrated application date/context behavior and final report separately. Recheck this evaluation and rerun affected tests after any behavioral patch.

## Related files

- [Taimoor's contribution](../contributions/taimoor/README.md)
- [Relational mapping and column dictionary](relational_mapping.md)
- [Integration contract](schema_integration.md)
- [Schema validation evidence](schema_validation_results.md)
- [Mason's dataset limitations](../contributions/mason/README.md#limits)

The assistant helped compare and document the user-supplied evaluation. The table's decisions are attributed to their supplied source; automated checks are attributed to their actual execution.
