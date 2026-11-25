"""Checks for the semantic layer: ontology shape and explicit graph rules.

Two kinds of test live here. Structural tests read the ontology file and assert
that it still mirrors the twelve accepted relations. Behavioural tests build a
small graph, mutate one thing, and assert that exactly the intended rule fires.

All fixture individuals are synthetic and are not the team's demonstration data.
Run from the repository root: python -m unittest discover -s tests -v
"""
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef  # noqa: E402
from rdflib.namespace import XSD  # noqa: E402

from dal.schema_validation import (  # noqa: E402
    disclosure_context as relational_disclosure_context,
    scheme_context as relational_scheme_context,
)
from dal.models.semantic.graph_validation import (  # noqa: E402
    ETF, EXPLICIT_RULES, OWL_ENFORCED_RULES, GraphModelError,
    collect_issues, describe_rule_split, disclosure_context, load_graph,
    scheme_context, validate_graph,
)

ONTOLOGY = ROOT / 'src/dal/models/semantic/etf_allocations.owl'
EX = Namespace('https://example.invalid/synthetic/')
URL = 'https://example.invalid/synthetic-disclosure.txt'
RETRIEVED = '2026-11-01T00:00:00.000000Z'

# Twelve accepted relations and the class that carries each relation's columns.
TABLES_TO_CLASSES = {
    'Customer': ETF.Customer,
    'ETFProvider': ETF.ETFProvider,
    'Portfolio': ETF.Portfolio,
    'ETF': ETF.ETF,
    'ETFIdentifier': ETF.ETFIdentifier,
    'Holding': ETF.Holding,
    'SourceDocument': ETF.SourceDocument,
    'AllocationDimension': ETF.AllocationDimension,
    'ClassificationScheme': ETF.ClassificationScheme,
    'AllocationCategory': ETF.AllocationCategory,
    'AllocationSnapshot': ETF.AllocationSnapshot,
    'AllocationEntry': ETF.AllocationEntry,
}

# Scalar columns of the accepted schema, one datatype property each.
EXPECTED_DATATYPE_PROPERTIES = {
    'recordId',
    'customerNumber', 'givenName', 'familyName', 'email',
    'legalName', 'registrationNumber', 'registrationJurisdiction', 'websiteUrl',
    'portfolioReference', 'portfolioName', 'baseCurrency',
    'fundName', 'domicileCountryCode', 'inceptionDate',
    'identifierScheme', 'identifierValue', 'exchangeContext',
    'weightFraction', 'holdingAsOfDate',
    'url', 'retrievedAt', 'publishedAt', 'capturedFileRef', 'documentTitle',
    'dimensionName',
    'schemeAuthority', 'schemeName', 'version', 'definitionUrl',
    'label', 'code', 'contextKey',
    'allocationAsOfDate', 'basisNote', 'coverageStatus', 'sourceLocator',
}

EXPECTED_OBJECT_PROPERTIES = {
    'owns', 'ownedBy', 'offeredBy', 'hasIdentifier', 'identifiesETF',
    'hasHolding', 'inPortfolio', 'holdsETF',
    'hasSnapshot', 'describesETF', 'hasDimension', 'supportedBy',
    'publishedBy', 'definedBy', 'hasEntry', 'inSnapshot', 'usesCategory',
}


def _domain_classes(graph, prop):
    """Classes named by rdfs:domain, expanding a union domain."""
    from rdflib.collection import Collection
    found = set()
    for domain in graph.objects(prop, RDFS.domain):
        if isinstance(domain, URIRef):
            found.add(domain)
            continue
        for members in graph.objects(domain, OWL.unionOf):
            found.update(Collection(graph, members))
    return found


def typed(graph, subject, rdf_type):
    graph.add((subject, RDF.type, rdf_type))


def valid_graph():
    """One consistent synthetic state covering the whole model."""
    graph = Graph()
    for prefix, iri in (('etf', ETF), ('ex', EX)):
        graph.bind(prefix, iri)

    typed(graph, EX.C1, ETF.Customer)
    graph.add((EX.C1, ETF.customerNumber, Literal('SYN-C1')))
    graph.add((EX.C1, ETF.givenName, Literal('Example')))
    graph.add((EX.C1, ETF.familyName, Literal('Customer')))

    typed(graph, EX.O1, ETF.ETFProvider)
    graph.add((EX.O1, ETF.legalName, Literal('Example Provider Ltd')))
    graph.add((EX.O1, ETF.registrationNumber, Literal('SYN-R1')))
    graph.add((EX.O1, ETF.registrationJurisdiction, Literal('SYNTHETIC-REGISTRY')))

    typed(graph, EX.P1, ETF.Portfolio)
    graph.add((EX.P1, ETF.portfolioReference, Literal('SYN-P1')))
    graph.add((EX.P1, ETF.portfolioName, Literal('Example Portfolio')))
    graph.add((EX.P1, ETF.baseCurrency, Literal('CAD')))
    graph.add((EX.P1, ETF.ownedBy, EX.C1))

    typed(graph, EX.F1, ETF.ETF)
    graph.add((EX.F1, ETF.fundName, Literal('Example ETF A')))
    graph.add((EX.F1, ETF.domicileCountryCode, Literal('CA')))
    graph.add((EX.F1, ETF.baseCurrency, Literal('CAD')))
    graph.add((EX.F1, ETF.offeredBy, EX.O1))

    typed(graph, EX.I1, ETF.ETFIdentifier)
    graph.add((EX.I1, ETF.identifierScheme, Literal('Ticker')))
    graph.add((EX.I1, ETF.identifierValue, Literal('EXA')))
    graph.add((EX.I1, ETF.exchangeContext, Literal('XTSX')))
    graph.add((EX.I1, ETF.identifiesETF, EX.F1))

    typed(graph, EX.H1, ETF.Holding)
    graph.add((EX.H1, ETF.inPortfolio, EX.P1))
    graph.add((EX.H1, ETF.holdsETF, EX.F1))
    graph.add((EX.H1, ETF.weightFraction, Literal('0.5', datatype=XSD.double)))
    graph.add((EX.H1, ETF.holdingAsOfDate, Literal('2026-11-01', datatype=XSD.date)))

    typed(graph, EX.D1, ETF.AllocationDimension)
    graph.add((EX.D1, ETF.dimensionName, Literal('Sector')))

    typed(graph, EX.S1, ETF.ClassificationScheme)
    graph.add((EX.S1, ETF.schemeAuthority, Literal('Synthetic Authority')))
    graph.add((EX.S1, ETF.schemeName, Literal('Synthetic Sector')))
    graph.add((EX.S1, ETF.version, Literal('v1')))

    typed(graph, EX.K1, ETF.AllocationCategory)
    graph.add((EX.K1, ETF.hasDimension, EX.D1))
    graph.add((EX.K1, ETF.label, Literal('Technology')))
    graph.add((EX.K1, ETF.code, Literal('SYN-TECH')))
    graph.add((EX.K1, ETF.contextKey,
               Literal(scheme_context('Synthetic Authority', 'Synthetic Sector', 'v1'))))
    graph.add((EX.K1, ETF.definedBy, EX.S1))

    typed(graph, EX.DOC1, ETF.SourceDocument)
    graph.add((EX.DOC1, ETF.publishedBy, EX.O1))
    graph.add((EX.DOC1, ETF.url, Literal(URL)))
    graph.add((EX.DOC1, ETF.retrievedAt, Literal(RETRIEVED)))
    graph.add((EX.DOC1, ETF.capturedFileRef, Literal('tests/fixtures/synthetic_disclosure.txt')))
    graph.add((EX.DOC1, ETF.documentTitle, Literal('Synthetic disclosure')))

    typed(graph, EX.SN1, ETF.AllocationSnapshot)
    graph.add((EX.SN1, ETF.describesETF, EX.F1))
    graph.add((EX.SN1, ETF.hasDimension, EX.D1))
    graph.add((EX.SN1, ETF.supportedBy, EX.DOC1))
    graph.add((EX.SN1, ETF.allocationAsOfDate, Literal('2026-11-01', datatype=XSD.date)))
    graph.add((EX.SN1, ETF.basisNote, Literal('Synthetic basis')))
    graph.add((EX.SN1, ETF.coverageStatus, Literal('Partial')))
    graph.add((EX.SN1, ETF.sourceLocator, Literal('sector-table')))

    typed(graph, EX.E1, ETF.AllocationEntry)
    graph.add((EX.E1, ETF.inSnapshot, EX.SN1))
    graph.add((EX.E1, ETF.usesCategory, EX.K1))
    graph.add((EX.E1, ETF.weightFraction, Literal('0.35', datatype=XSD.double)))

    return graph


class OntologyStructureTests(unittest.TestCase):
    """The ontology must still mirror the twelve accepted relations."""

    @classmethod
    def setUpClass(cls):
        cls.graph = load_graph(ONTOLOGY)

    def test_parses_and_declares_version(self):
        self.assertGreater(len(self.graph), 300)
        ontology = next(self.graph.subjects(RDF.type, OWL.Ontology))
        self.assertEqual(str(ontology), str(ETF)[:-1])
        self.assertTrue(list(self.graph.objects(ontology, OWL.versionInfo)))

    def test_one_class_per_relation(self):
        classes = {c for c in self.graph.subjects(RDF.type, OWL.Class)
                   if isinstance(c, URIRef) and str(c).startswith(str(ETF))}
        self.assertEqual(classes, set(TABLES_TO_CLASSES.values()))
        self.assertEqual(len(classes), 12)

    def test_no_individuals_in_the_schema_file(self):
        for relation in TABLES_TO_CLASSES.values():
            self.assertEqual(list(self.graph.subjects(RDF.type, relation)), [])

    def test_every_class_is_documented(self):
        for relation in TABLES_TO_CLASSES.values():
            self.assertTrue(list(self.graph.objects(relation, RDFS.label)), relation)
            self.assertTrue(list(self.graph.objects(relation, RDFS.comment)), relation)

    def test_property_inventory(self):
        datatype = {str(p).rsplit('#', 1)[1]
                    for p in self.graph.subjects(RDF.type, OWL.DatatypeProperty)}
        self.assertEqual(datatype, EXPECTED_DATATYPE_PROPERTIES)
        obj = {str(p).rsplit('#', 1)[1]
               for p in self.graph.subjects(RDF.type, OWL.ObjectProperty)}
        self.assertEqual(obj, EXPECTED_OBJECT_PROPERTIES)
        self.assertEqual(len(datatype), 37)
        self.assertEqual(len(obj), 17)

    def test_every_property_has_domain_and_range(self):
        for kind in (OWL.DatatypeProperty, OWL.ObjectProperty):
            for prop in self.graph.subjects(RDF.type, kind):
                self.assertTrue(list(self.graph.objects(prop, RDFS.domain)), prop)
                self.assertTrue(list(self.graph.objects(prop, RDFS.range)), prop)

    def test_datatype_properties_sit_on_the_matching_class(self):
        expected = {
            ETF.customerNumber: {ETF.Customer}, ETF.givenName: {ETF.Customer},
            ETF.familyName: {ETF.Customer}, ETF.email: {ETF.Customer},
            ETF.legalName: {ETF.ETFProvider},
            ETF.registrationNumber: {ETF.ETFProvider},
            ETF.registrationJurisdiction: {ETF.ETFProvider},
            ETF.websiteUrl: {ETF.ETFProvider},
            ETF.portfolioReference: {ETF.Portfolio},
            ETF.portfolioName: {ETF.Portfolio},
            ETF.baseCurrency: {ETF.Portfolio, ETF.ETF},
            ETF.fundName: {ETF.ETF}, ETF.domicileCountryCode: {ETF.ETF},
            ETF.inceptionDate: {ETF.ETF},
            ETF.identifierScheme: {ETF.ETFIdentifier},
            ETF.identifierValue: {ETF.ETFIdentifier},
            ETF.exchangeContext: {ETF.ETFIdentifier},
            ETF.weightFraction: {ETF.Holding, ETF.AllocationEntry},
            ETF.holdingAsOfDate: {ETF.Holding},
            ETF.url: {ETF.SourceDocument}, ETF.retrievedAt: {ETF.SourceDocument},
            ETF.publishedAt: {ETF.SourceDocument},
            ETF.capturedFileRef: {ETF.SourceDocument},
            ETF.documentTitle: {ETF.SourceDocument},
            ETF.dimensionName: {ETF.AllocationDimension},
            ETF.schemeAuthority: {ETF.ClassificationScheme},
            ETF.schemeName: {ETF.ClassificationScheme},
            ETF.version: {ETF.ClassificationScheme},
            ETF.definitionUrl: {ETF.ClassificationScheme},
            ETF.label: {ETF.AllocationCategory},
            ETF.code: {ETF.AllocationCategory},
            ETF.contextKey: {ETF.AllocationCategory},
            ETF.allocationAsOfDate: {ETF.AllocationSnapshot},
            ETF.basisNote: {ETF.AllocationSnapshot},
            ETF.coverageStatus: {ETF.AllocationSnapshot},
            ETF.sourceLocator: {ETF.AllocationSnapshot},
            ETF.recordId: set(TABLES_TO_CLASSES.values()),
        }
        for prop, owners in expected.items():
            self.assertTrue(owners <= _domain_classes(self.graph, prop), (prop, owners))

    def test_association_classes_keep_their_own_attributes(self):
        for relation, weight, as_of in (
            (ETF.Holding, ETF.weightFraction, ETF.holdingAsOfDate),
            (ETF.AllocationEntry, ETF.weightFraction, None),
        ):
            self.assertIn(relation, _domain_classes(self.graph, weight))
            if as_of is not None:
                self.assertIn(relation, _domain_classes(self.graph, as_of))

    def test_reused_fibo_classes(self):
        expected = {
            ETF.Portfolio: 'FND/OwnershipAndControl/Ownership/Portfolio',
            ETF.Holding: 'FND/OwnershipAndControl/Ownership/Holding',
            ETF.AllocationSnapshot: 'FBC/ProductsAndServices/FinancialProductsAndServices/WeightedBasket',
            ETF.AllocationEntry: 'FBC/ProductsAndServices/FinancialProductsAndServices/WeightedBasketConstituent',
            ETF.ClassificationScheme: 'SEC/Funds/CollectiveInvestmentVehicles/FundClassificationScheme',
            ETF.AllocationCategory: 'SEC/Funds/CollectiveInvestmentVehicles/FundClassification',
        }
        for local, fragment in expected.items():
            parents = {str(p) for p in self.graph.objects(local, RDFS.subClassOf)
                       if isinstance(p, URIRef)}
            self.assertTrue(any(fragment in p for p in parents), (local, parents))

    def test_fibo_is_referenced_not_imported(self):
        ontology = next(self.graph.subjects(RDF.type, OWL.Ontology))
        self.assertEqual(list(self.graph.objects(ontology, OWL.imports)), [],
                         'FIBO must stay an external reference so the file works offline')

    def test_keys_and_disjointness(self):
        keyed = {str(c).rsplit('#', 1)[1] for c in self.graph.subjects(OWL.hasKey, None)}
        self.assertEqual(keyed, {'Customer', 'ETFProvider', 'ETFIdentifier', 'AllocationDimension'})
        pairs = {(str(s).rsplit('#', 1)[1], str(o).rsplit('#', 1)[1])
                 for s, o in self.graph.subject_objects(OWL.disjointWith)}
        self.assertIn(('Portfolio', 'ETF'), pairs)
        self.assertIn(('AllocationSnapshot', 'AllocationEntry'), pairs)

    def test_dimension_chain_axiom(self):
        from rdflib.collection import Collection
        head = next(self.graph.objects(ETF.hasDimension, OWL.propertyChainAxiom))
        members = Collection(self.graph, head)
        self.assertEqual([str(p).rsplit('#', 1)[1] for p in members],
                         ['hasEntry', 'usesCategory', 'hasDimension'])


class ContextKeyParityTests(unittest.TestCase):
    """The graph helper must produce the same context keys as the relational one."""

    def test_scheme_context_matches_relational_implementation(self):
        self.assertEqual(
            scheme_context('Synthetic Authority', 'Synthetic Sector', 'v1'),
            relational_scheme_context('Synthetic Authority', 'Synthetic Sector', 'v1'),
        )

    def test_disclosure_context_matches_relational_implementation(self):
        self.assertEqual(
            disclosure_context(URL, RETRIEVED, 'geography-table', 'Geography'),
            relational_disclosure_context(URL, RETRIEVED, 'geography-table', 'Geography'),
        )

    def test_context_rejects_blank_components(self):
        with self.assertRaises(ValueError):
            scheme_context('Synthetic Authority', '  ', 'v1')


class GraphRuleTests(unittest.TestCase):
    """Mutating one thing must fire exactly the intended rule."""

    def assertOnlyIssue(self, graph, fragment, **kwargs):
        issues = collect_issues(graph, **kwargs)
        self.assertTrue(issues, 'expected a violation')
        self.assertTrue(any(fragment in issue for issue in issues), issues)

    def assertClean(self, graph, **kwargs):
        self.assertEqual(collect_issues(graph, **kwargs), [])

    def test_valid_state_has_no_issues(self):
        self.assertClean(valid_graph())

    def test_valid_state_with_capture_root(self):
        self.assertClean(valid_graph(), capture_root=ROOT)

    def test_capture_file_missing(self):
        graph = valid_graph()
        graph.set((EX.DOC1, ETF.capturedFileRef, Literal('tests/fixtures/does-not-exist.txt')))
        self.assertOnlyIssue(graph, 'retained capture', capture_root=ROOT)

    def test_capture_path_escaping_root(self):
        graph = valid_graph()
        graph.set((EX.DOC1, ETF.capturedFileRef, Literal('../outside.txt')))
        self.assertOnlyIssue(graph, 'retained capture', capture_root=ROOT)

    def test_complete_total_outside_tolerance(self):
        graph = valid_graph()
        graph.set((EX.SN1, ETF.coverageStatus, Literal('Complete')))
        self.assertOnlyIssue(graph, 'complete total is 0.35')

    def test_complete_total_inside_tolerance(self):
        graph = valid_graph()
        graph.set((EX.SN1, ETF.coverageStatus, Literal('Complete')))
        graph.set((EX.E1, ETF.weightFraction, Literal('0.9975', datatype=XSD.double)))
        self.assertClean(graph)

    def test_complete_total_boundary_is_tolerated(self):
        graph = valid_graph()
        graph.set((EX.SN1, ETF.coverageStatus, Literal('Complete')))
        graph.set((EX.E1, ETF.weightFraction, Literal('0.995', datatype=XSD.double)))
        self.assertClean(graph)

    def test_complete_total_just_outside_boundary(self):
        graph = valid_graph()
        graph.set((EX.SN1, ETF.coverageStatus, Literal('Complete')))
        graph.set((EX.E1, ETF.weightFraction, Literal('0.9949', datatype=XSD.double)))
        self.assertOnlyIssue(graph, 'complete total')

    def test_partial_total_is_not_constrained(self):
        graph = valid_graph()
        graph.set((EX.SN1, ETF.coverageStatus, Literal('Partial')))
        graph.set((EX.E1, ETF.weightFraction, Literal('0.2', datatype=XSD.double)))
        self.assertClean(graph)

    def test_weight_above_one(self):
        graph = valid_graph()
        graph.set((EX.E1, ETF.weightFraction, Literal('1.4', datatype=XSD.double)))
        self.assertOnlyIssue(graph, 'outside [0, 1]')

    def test_weight_negative(self):
        graph = valid_graph()
        graph.set((EX.H1, ETF.weightFraction, Literal('-0.1', datatype=XSD.double)))
        self.assertOnlyIssue(graph, 'weight fraction -0.1')

    def test_weight_not_a_number(self):
        graph = valid_graph()
        graph.set((EX.E1, ETF.weightFraction, Literal('thirty percent')))
        self.assertOnlyIssue(graph, 'is not a number')

    def test_dimension_mismatch(self):
        graph = valid_graph()
        typed(graph, EX.D2, ETF.AllocationDimension)
        graph.add((EX.D2, ETF.dimensionName, Literal('Geography')))
        graph.set((EX.K1, ETF.hasDimension, EX.D2))
        self.assertOnlyIssue(graph, 'differs from snapshot dimension')

    def test_dimension_name_not_permitted(self):
        graph = valid_graph()
        graph.set((EX.D1, ETF.dimensionName, Literal('AssetClass')))
        self.assertOnlyIssue(graph, 'dimension name')

    def test_coverage_status_not_permitted(self):
        graph = valid_graph()
        graph.set((EX.SN1, ETF.coverageStatus, Literal('Estimated')))
        self.assertOnlyIssue(graph, 'coverage status')

    def test_fund_without_identifier(self):
        graph = valid_graph()
        graph.remove((EX.F1, ETF.hasIdentifier, EX.I1))
        graph.remove((EX.I1, ETF.identifiesETF, EX.F1))
        self.assertOnlyIssue(graph, 'at least one identifier is required')

    def test_snapshot_without_entry(self):
        graph = valid_graph()
        graph.remove((EX.E1, ETF.inSnapshot, EX.SN1))
        self.assertOnlyIssue(graph, 'at least one entry is required')

    def test_isin_shape_and_exchange_context(self):
        graph = valid_graph()
        graph.set((EX.I1, ETF.identifierScheme, Literal('ISIN')))
        graph.set((EX.I1, ETF.identifierValue, Literal('CA1234567890')))
        self.assertOnlyIssue(graph, 'ISIN must not carry an exchange context')

    def test_isin_value_shape(self):
        graph = valid_graph()
        graph.set((EX.I1, ETF.identifierScheme, Literal('ISIN')))
        graph.remove((EX.I1, ETF.exchangeContext, None))
        graph.set((EX.I1, ETF.identifierValue, Literal('CA1234')))
        self.assertOnlyIssue(graph, 'wrong shape')

    def test_ticker_requires_exchange(self):
        graph = valid_graph()
        graph.remove((EX.I1, ETF.exchangeContext, None))
        self.assertOnlyIssue(graph, 'ticker requires an exchange context')

    def test_context_key_mismatch(self):
        graph = valid_graph()
        graph.set((EX.K1, ETF.contextKey, Literal('scheme:["Synthetic Authority","Synthetic Sector","v2"]')))
        self.assertOnlyIssue(graph, 'does not match its scheme edition')

    def test_context_key_accepts_disclosure_form_without_scheme(self):
        graph = valid_graph()
        graph.remove((EX.K1, ETF.definedBy, EX.S1))
        graph.set((EX.K1, ETF.contextKey,
                   Literal(disclosure_context(URL, RETRIEVED, 'sector-table', 'Sector'))))
        self.assertClean(graph)

    def test_single_valued_property_clash(self):
        graph = valid_graph()
        typed(graph, EX.C2, ETF.Customer)
        graph.add((EX.C2, ETF.customerNumber, Literal('SYN-C2')))
        graph.add((EX.P1, ETF.ownedBy, EX.C2))
        self.assertOnlyIssue(graph, 'ownedBy has more than one value')

    def test_duplicate_disclosure_block(self):
        graph = valid_graph()
        typed(graph, EX.SN2, ETF.AllocationSnapshot)
        for prop in (ETF.describesETF, ETF.hasDimension, ETF.supportedBy,
                     ETF.allocationAsOfDate, ETF.coverageStatus, ETF.sourceLocator):
            for value in graph.objects(EX.SN1, prop):
                graph.add((EX.SN2, prop, value))
        self.assertOnlyIssue(graph, 'duplicates the disclosure block')

    def test_missing_required_attribute(self):
        graph = valid_graph()
        graph.remove((EX.SN1, ETF.basisNote, None))
        self.assertOnlyIssue(graph, 'AllocationSnapshot requires basisNote')

    def test_missing_required_link(self):
        graph = valid_graph()
        graph.remove((EX.E1, ETF.usesCategory, EX.K1))
        self.assertOnlyIssue(graph, 'AllocationEntry requires usesCategory')

    def test_retrieved_at_must_be_utc(self):
        graph = valid_graph()
        graph.set((EX.DOC1, ETF.retrievedAt, Literal('2026-11-01 00:00:00')))
        self.assertOnlyIssue(graph, 'is not a valid UTC dateTime')

    def test_as_of_date_must_be_valid(self):
        graph = valid_graph()
        graph.set((EX.SN1, ETF.allocationAsOfDate, Literal('2026-13-45')))
        self.assertOnlyIssue(graph, 'is not a valid date')

    def test_tolerance_is_validated(self):
        for bad in (-0.1, 1.0, float('nan')):
            with self.assertRaises(ValueError):
                collect_issues(valid_graph(), total_tolerance=bad)

    def test_validate_graph_raises_with_all_messages(self):
        graph = valid_graph()
        graph.set((EX.E1, ETF.weightFraction, Literal('1.4', datatype=XSD.double)))
        graph.set((EX.SN1, ETF.coverageStatus, Literal('Complete')))
        with self.assertRaises(GraphModelError) as caught:
            validate_graph(graph)
        message = str(caught.exception)
        self.assertIn('outside [0, 1]', message)
        self.assertIn('complete total', message)

    def test_rule_split_is_documented(self):
        self.assertGreaterEqual(len(OWL_ENFORCED_RULES), 5)
        self.assertGreaterEqual(len(EXPLICIT_RULES), 8)
        report = describe_rule_split()
        self.assertIn('Expressed in the ontology', report)
        self.assertIn('Requires explicit validation', report)

    def test_cli_reports_failure(self):
        from dal.models.semantic.graph_validation import main
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / 'bad.ttl'
            graph = valid_graph()
            graph.set((EX.E1, ETF.weightFraction, Literal('1.4', datatype=XSD.double)))
            graph.serialize(destination=str(bad), format='turtle')
            self.assertEqual(main([str(bad)]), 1)
            good = Path(directory) / 'good.ttl'
            valid_graph().serialize(destination=str(good), format='turtle')
            self.assertEqual(main([str(good)]), 0)
            self.assertEqual(main(['--rules']), 0)


class BackendAlignmentTests(unittest.TestCase):
    """The package must line up with the accepted backend, not only with the schema.

    These tests skip when the backend modules or its exported ABox are absent (for
    example in a standalone checkout of Mason's contribution). They run as soon as
    the package is applied on top of the Milestone 5 branch.
    """

    VOCABULARY = ROOT / 'src' / 'semantic' / 'vocabulary.py'
    DEMO = ROOT / 'milestones' / '05_semantic' / 'data' / 'demo.rdf'

    def test_namespace_matches_backend_vocabulary(self):
        if not self.VOCABULARY.is_file():
            self.skipTest('backend vocabulary not present in this checkout')
        text = self.VOCABULARY.read_text(encoding='utf-8')
        base = re.search(r'BASE = "([^"]+)"', text).group(1)
        local = re.search(r'NS = BASE \+ "([^"]+)"', text).group(1)
        self.assertEqual(base + local, str(ETF),
                         'Mason ontology and Taimoor vocabulary must share one namespace')

    def test_demo_abox_validates_clean(self):
        if not self.DEMO.is_file():
            self.skipTest('backend ABox export not present in this checkout')
        graph = load_graph(self.DEMO)
        self.assertGreaterEqual(len(graph), 300)
        self.assertEqual(collect_issues(graph), [])

    def test_abox_uses_only_declared_terms(self):
        if not self.DEMO.is_file():
            self.skipTest('backend ABox export not present in this checkout')
        ontology = load_graph(ONTOLOGY)
        declared = {str(p) for kind in (OWL.DatatypeProperty, OWL.ObjectProperty)
                    for p in ontology.subjects(RDF.type, kind)}
        classes = {str(c) for c in ontology.subjects(RDF.type, OWL.Class)
                   if isinstance(c, URIRef) and str(c).startswith(str(ETF))}
        graph = load_graph(self.DEMO)
        self.assertEqual({str(p) for p in graph.predicates()
                          if str(p).startswith(str(ETF))} - declared, set())
        self.assertEqual({str(o) for o in graph.objects(None, RDF.type)
                          if str(o).startswith(str(ETF))} - classes, set())

    def test_bridge_validates_pyoxigraph_candidate(self):
        try:
            from pyoxigraph import RdfFormat, Store
        except ImportError:  # pragma: no cover - optional backend dependency
            self.skipTest('pyoxigraph not installed')
        if not self.DEMO.is_file():
            self.skipTest('backend ABox export not present in this checkout')
        from dal.models.semantic.backend_bridge import (
            DATA_GRAPH, validate_candidate_store,
        )
        from dal.schema_validation import ModelIntegrityError

        store = Store()
        store.load(path=str(self.DEMO), format=RdfFormat.RDF_XML)
        self.assertIsNone(validate_candidate_store(store))

        entry = 'https://github.com/Pyrex111/CSC501_Data_Modeling_Project/resource/AllocationEntry/1'
        store.update(
            f'INSERT DATA {{ GRAPH <{DATA_GRAPH}> {{ <{entry}> '
            f'<{str(ETF)}weightFraction> "2.0"^^<http://www.w3.org/2001/XMLSchema#double> }} }}'
        )
        with self.assertRaises(ModelIntegrityError):
            validate_candidate_store(store)


if __name__ == '__main__':
    unittest.main()
