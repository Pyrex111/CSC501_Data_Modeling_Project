# Taimoor's report contribution

These are inputs to the team's final ACM sigconf report, not a complete submission.

| File | Use |
| --- | --- |
| [taimoor_relational_section.tex](taimoor_relational_section.tex) | Main-relations, identification and schema-integrity explanation for the two report pages |
| [mason_query_dml_section.tex](mason_query_dml_section.tex) | Mason's query, DML-integrity and reproducibility discussion for the two report pages |
| [taimoor_references.bib](taimoor_references.bib) | Official SQLite references cited by that section; merge with the team bibliography |
| [relations_constraints.tex](relations_constraints.tex) | All twelve relations, attributes, keys and other integrity rules for the third page |
| [relations_constraints_preview.tex](relations_constraints_preview.tex) | Standalone two-column review wrapper requiring an installed ACM template/class |
| [relations_constraints_preview.pdf](relations_constraints_preview.pdf) | One-page visual preview of the relation/constraint listing |

In the team's current ACM sigconf source, insert Taimoor's section at the appropriate place alongside Mason's query discussion and Shahmeer's application material. After the two report pages, use:

```tex
\clearpage
\input{relations_constraints}
```

Adjust input paths for the team's source layout. The listing's internal `\newpage` moves to its second column when used in a two-column report. Include it at the start of page 3. It assumes no prior definition of its local `\rel` macro.

The preview was compiled using the acmart class supplied in the illustrative sample ZIP. Some ACM font packages were unavailable in the runtime, so the preview uses fallback fonts. It checks content fit and legibility; compile the final report in the current ACM template and verify exactly two text/report pages plus one relation/constraint page. Do not treat this standalone preview as the final team report.

The report section accurately describes the schema tests and explicitly distinguishes them from application/data evaluation. Update the test count if the suite changes, and rewrite claims if the implementation changes. Each member must review the resulting prose and disclose AI assistance as required by the manual.
