# CSC501 Data Modeling Project

**Extending the Financial Industry Business Ontology to Represent Time-Varying Exchange-Traded Fund Allocations**

University of Victoria, CSC501: Algorithms and Data Models, Fall 2026.

Team: Taimoor Shahzad, Mason Li, and M. Shahmeer Ather Kakwan.

## Project scope

We model dated sector and geographic allocation percentages published by ETF providers. The conceptual model separates a customer's dated ETF holding from a provider's dated allocation disclosure, and connects that disclosure to its entries, category meanings and captured source. FIBO and prior GFRO work inform the design. Relational implementation is in preparation for Milestone 4; knowledge-graph implementation and evaluation follow in later project stages.

## Start here

| Artifact | Location |
| --- | --- |
| Current revised conceptual ERD and business identity rules, PDF | [Milestone 4 ERD](milestones/04_relational/figures/etf_allocation_erd_revised.pdf) |
| Editable current ERD, diagrams.net | [Milestone 4 ERD source](milestones/04_relational/figures/etf_allocation_erd.drawio) |
| Milestone 4 model changes, responsibilities and implementation plan | [Team handoff](milestones/04_relational/docs/milestone4_handoff.md) |
| Historical Milestone 2 conceptual ERD | [Milestone 2 ERD](milestones/02_background/figures/etf_allocation_erd.pdf) |
| Milestone 2 compiled report and appendix | [Report PDF](milestones/02_background/submission/2_Background.pdf) |
| Milestone 2 source and submission package | [Source ZIP](milestones/02_background/submission/2_Background_Taimoor_Mason_Shahmeer.zip) |
| Current reviewed Milestone 3 slide | [One-slide PDF](milestones/03_3mt/slides/3_3MT.pdf) |
| Taimoor's Milestone 3 opening | [Edited spoken draft](milestones/03_3mt/contributions/taimoor/opening_edited.md) |
| Milestone descriptions and navigation | [Milestones index](milestones/README.md) |

The current ERD was revised on 30 October 2026 for Milestone 4 preparation. Its second page/tab documents business identity, scoped uniqueness and prototype assumptions. The Milestone 2 ERD remains available as the historical model; the Milestone 3 slide is a simplified view of that earlier design. The current ERD is a conceptual design, and a relational schema and runnable implementation are still to be developed.

## Repository organization

| Directory | Purpose |
| --- | --- |
| [milestones/02_background](milestones/02_background/README.md) | Literature review, full ERD, compiled report, source package and member contributions |
| [milestones/03_3mt](milestones/03_3mt/README.md) | One-slide talk, spoken drafts and contribution records |
| [milestones/04_relational](milestones/04_relational/README.md) | Revised conceptual ERD, business identity rules and implementation handoff |

Within each milestone, shared deliverables are separated from member working drafts. The Milestone 2 source ZIP includes LaTeX, bibliography, figures, preserved drafts and build instructions. The existing member folders retain their original names and history.

## Contributions and editing

Each team member should commit substantive work through their own GitHub account. Shared artifact uploads may be made by the coordinator, so file creation and Git commit authorship should be read together with the contribution notes.

Taimoor leads the opening and presentation model visualization for Milestone 3. Shahmeer presents the gap, model and knowledge-graph direction. Mason assembled the slide and revised its layout. The slide is credited to Mason even though this shared PDF is uploaded by Taimoor.

Supplied original drafts and AI-assisted edited versions are labelled separately. Preserve the Milestone 2 and 3 originals for their editing records. Milestone 4 permits AI task completion with human evaluation; its [handoff](milestones/04_relational/docs/milestone4_handoff.md#ai-use-record) records AI assistance and the team's required review and validation.

## Current status

Milestone 2 artifacts are available above. The reviewed Milestone 3 slide and Taimoor's opening are available. [Shahmeer's original and revised scripts](milestones/03_3mt/contributions/shahmeer/) and [Mason's editable slides](milestones/03_3mt/contributions/Mason/) are available in their contribution folders. Taimoor's current Word draft and matching Markdown script are in his Milestone 3 contribution folder. The final Milestone 3 submission ZIP and editing appendix are not yet recorded here.

Milestone 4 preparation now includes the [revised ERD and business identity rules](milestones/04_relational/figures/etf_allocation_erd_revised.pdf), [editable Draw.io source](milestones/04_relational/figures/etf_allocation_erd.drawio), and [team handoff](milestones/04_relational/docs/milestone4_handoff.md). No Milestone 4 application, SQL implementation or final report is included yet.
