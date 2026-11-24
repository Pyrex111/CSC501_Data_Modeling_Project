# FIBO Alignment

Milestone 5, semantic layer. Owner: Mason Li (ontology and semantic validation),
with AI assistance disclosed in the contribution notes.

This note records what we reuse from FIBO, what we extend, and what we looked at
and decided not to use. The third list matters as much as the first two: the
marking scheme rewards a defended boundary, and an ontology that subclasses
everything it can find claims more than the evidence supports.

Evidence base: `milestones/02_background/contributions/taimoor/FIBO_evidence.md`
catalogues the FIBO modules quoted below with the axiom fragments retrieved on
2026-10-01 from revision `9a7b90c`. The IRIs are copied from that file.

Version 1.1.0 differs from the first draft in one place only: the two weight
properties were merged into `etf:weightFraction` when the vocabulary was aligned
with the accepted ABox (see `docs/backend_alignment.md`), so the fractional-interest
claim is withdrawn and explained in section 2.

## 1. Reused classes

| Local class | FIBO parent | Why it fits |
| --- | --- | --- |
| `etf:Portfolio` | `fibo:Portfolio` (FND/OwnershipAndControl/Ownership) | FIBO defines a portfolio as a collection that comprises holdings and is a member of at most one portfolio. The accepted relation holds the same shape: a customer's portfolio of dated holdings, not nested inside another portfolio. |
| `etf:Holding` | `fibo:Holding` (FND/OwnershipAndControl/Ownership) | FIBO defines a holding as a financial interest in an asset or security, with an optional fractional interest. Our association class carries exactly that plus a date, and the weight is the fractional interest. |
| `etf:AllocationSnapshot` | `fibo:WeightedBasket` (FBC/ProductsAndServices/FinancialProductsAndServices) | FIBO describes a weighted basket as a structured collection whose members are weighted constituents. A dated allocation block is a basket of categories with weights. |
| `etf:AllocationEntry` | `fibo:WeightedBasketConstituent` | FIBO requires a weighted constituent to carry exactly one weight; our entry carries one weight and belongs to one snapshot. |
| `etf:ClassificationScheme` | `fibo:FundClassificationScheme` (SEC/Funds/CollectiveInvestmentVehicles) | FIBO defines a fund classification scheme as a classification scheme that defines fund classifications. That is precisely the authority/name/version record we keep. |
| `etf:AllocationCategory` | `fibo:FundClassification` | FIBO defines a fund classification as a published code that classifies a fund by asset class. A sector or geographic label scoped to one edition is the same kind of thing. |
| `etf:ETF` | `fibo:CollectiveInvestmentVehicle` (SEC/Securities/Pools) | The closest published class for a pooled vehicle whose units are traded. We do not claim the fund is a security; we claim it is a collective investment vehicle, which is the weaker and better supported statement. |

Seven subsumption axioms, one per non-association entity class plus the two
association classes.

## 2. Reused properties

| Local property | FIBO or Commons super-property | Note |
| --- | --- | --- |
| `etf:weightFraction` | `fibo:hasWeight` (FND/Utilities/Analytics) | The weight of a basket constituent in its basket. One accepted column serves both holdings and entries, so only the generic weight claim is made. |
| `etf:allocationAsOfDate` | `fibo:hasAsOfDate` (FND/DatesAndTimes/FinancialDates) | FIBO distinguishes the date on which information is valid from the date it was created. Every as-of column here is the first kind. |
| `etf:holdingAsOfDate` | `fibo:hasAsOfDate` | Same distinction on the customer side; the two dates are deliberately independent. |
| `etf:hasEntry` | `cmns:hasMember` (OMG Commons/Collections) | Entries are members of a snapshot collection. |
| `etf:hasHolding` | `cmns:comprises` | FIBO's portfolio axiom uses `comprises` for the portfolio-to-holding direction, so declaring the sub-property keeps the reused class consistent with its own parent. |

`cmns:hasMember` and `cmns:comprises` are the OMG Commons collection properties
that FIBO itself builds on, so using them keeps our collection axioms compatible
with the modules we reuse.

**Why `hasFractionalInterest` is no longer claimed.** The first draft declared
`etf:holdingWeight ⊑ fibo:hasFractionalInterest` and kept the entry weight separate
as `etf:declaredWeight ⊑ fibo:hasWeight`. The accepted ABox writes both columns as
the same predicate, `weightFraction`, so keeping two local properties would have
left both restrictions unpopulated and made the stronger claim apply to allocation
entries it does not fit: a provider's published share of a basket is not a customer's
fractional ownership interest. Merging is the honest option, and the price is one
FIBO claim instead of two. The role distinction survives at the class level, where a
reader can still see that `Holding` and `AllocationEntry` are different things.

## 3. Considered and rejected

**`SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentPolicy` and
`.../FundPortfolioInvestmentLimitations`.** These are the most tempting candidates:
FIBO describes an investment policy that `definesAllocations` to a set of
limitations, which reads like "a portfolio with percentage allocations". It is not
the same claim. FIBO's policy states how a portfolio is intended to be configured in
order to meet its objective — a target, set by the manager. Our `AllocationSnapshot`
records what a provider disclosed on a given date, including cases where coverage is
`Partial` or `Unknown` and the published weights do not add up to one. Asserting
`AllocationSnapshot ⊑ FundPortfolioInvestmentPolicy` would say that an observed,
possibly incomplete disclosure is a manager's intended policy, which inverts the
meaning of the data and would license inferences about intent that the evidence does
not support. This boundary is the central extension argument in the report: FIBO
models the plan, we model the observation, and the difference is the gap we fill.

**`BE/FunctionalEntities/Publishers/Publisher`.** `etf:ETFProvider` is the object of
`offeredBy` from a fund and of `publishedBy` from a source document. FIBO's Publisher
is a party role played by a party that prints or distributes something. A single row
in `ETFProvider` plays both the issuer role and the publisher role here, and FIBO
models roles as separate resources played by a party. Subsuming our class under the
publisher role would assert that the legal entity *is* a publisher role, mixing an
entity with a role. The correct FIBO-shaped treatment would be two role individuals
over one party, which is a modelling change we are not making in this milestone. We
record the rejection rather than the compromise.

**`FBC/.../BasketConstituent`.** `WeightedBasketConstituent` already subsumes it, so
an explicit second subsumption adds nothing and would duplicate the hierarchy.

## 4. Extensions, and where FIBO has no class

| Local term | FIBO status | Justification |
| --- | --- | --- |
| `etf:Customer` | no retail account class at this granularity | FIBO models parties and roles, not a person's labelled portfolio collection. |
| `etf:ETFProvider` | see rejection above | Needed as the issuer-and-publisher anchor; kept as an extension so the role question stays visible. |
| `etf:ETFIdentifier` | no class for "ISIN or ticker with an exchange context" | FIBO has identifier infrastructure, but the two-shape rule (ISIN global, ticker exchange-scoped) is ours and is what makes uniqueness work. |
| `etf:SourceDocument` | no capture/provenance pair | FIBO describes documents and publishers, not "the file we retained and when we took it". Provenance is the point of this model. |
| `etf:AllocationDimension` | no class | The axis of the disclosure (Sector, Geography) is a reporting concept, not a FIBO concept. |
| `coverageStatus`, `basisNote`, `sourceLocator`, `contextKey` | no equivalents | These carry the honesty of the observation: how complete it is, what basis was printed, where in the capture it sits, and which edition the labels belong to. |
| `recordId` | no equivalent, and none wanted | A local row handle for the application, not a semantic identifier. |

## 5. What this buys, and what it does not

Reuse buys interoperability at the class level: a query written against
`fibo:WeightedBasket` will also find our snapshots, and a consumer that knows
`fibo:hasAsOfDate` can read our dates without learning our vocabulary. Reuse does
not buy instance-level agreement — no FIBO individual is asserted equal to any of
ours, no `owl:imports` closure is shipped, and the weight literals are `xsd:double`
because that is what the accepted store writes, not what a FIBO example would use.

The honest summary for the report is that the alignment is a set of *subsumption
claims with two deliberate refusals*, not a claim that this model is a FIBO profile.
