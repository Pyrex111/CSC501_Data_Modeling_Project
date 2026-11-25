"""Graph-backed equivalent of the accepted DAL; reads/writes execute SPARQL.

SQL is never used to answer these operations. Error classes and result keys are
shared with M4 so Shahmeer can adapt the UI without rewriting form contracts.
"""

from pyoxigraph import Literal, NamedNode, Store

from dal.repositories import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
    _validate_weight,
)
from dal.repositories import (
    RepositoryError as RepositoryError,
)
from dal.schema_validation import ModelIntegrityError

from .codec import record_quads
from .store import block, select
from .vocabulary import DATA_GRAPH, NS, SCHEMA, XSD, predicate, resource


def entity(table, variable, fields):
    spec = {c["name"]: c for c in SCHEMA[table]["columns"]}
    parts = [f"?{variable} a <{NS}{table}> ."]
    for column, output in fields.items():
        triple = f"?{variable} {predicate(table, column)} ?{output} ."
        c = spec[column]
        parts.append(
            triple if c["notnull"] or c["pk"] else "OPTIONAL { " + triple + " }"
        )
    return "\n".join(parts)


def ticker_pattern(etf="_etf", name="Ticker"):
    # Use the same exchange/value ordering as M4, even with multiple listings.
    return f"""OPTIONAL {{
      ?identifier a <{NS}ETFIdentifier>; <{NS}identifiesETF> ?{etf};
          <{NS}identifierScheme> "Ticker"; <{NS}identifierValue> ?{name};
          <{NS}exchangeContext> ?ExchangeContext .
      FILTER NOT EXISTS {{ ?other a <{NS}ETFIdentifier>;
          <{NS}identifiesETF> ?{etf}; <{NS}identifierScheme> "Ticker";
          <{NS}exchangeContext> ?ox; <{NS}identifierValue> ?ov .
          FILTER (?ox < ?ExchangeContext || (?ox = ?ExchangeContext && ?ov < ?{name})) }}
    }}"""


def query(target, columns, patterns, filters="", order=""):
    sparql = (
        "SELECT "
        + " ".join("?" + c for c in columns)
        + f" WHERE {{ GRAPH {DATA_GRAPH} {{\n"
        + "\n".join(patterns)
        + "\n"
        + filters
        + "\n} } "
        + order
    )
    return (
        select(target, sparql) if isinstance(target, Store) else target.select(sparql)
    )


def id_filter(variable, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("Record IDs must be integers.")
    return f"FILTER (?{variable} = {value})"


def text_filter(variable, value):
    return f"FILTER (STR(?{variable}) = {Literal(str(value))})"


def search_disclosures(
    db,
    ticker=None,
    dimension_name=None,
    as_of_date=None,
    *,
    etf_id=None,
    allocation_dimension_id=None,
):
    cols = [
        "SnapshotId",
        "ETFId",
        "Ticker",
        "ExchangeContext",
        "FundName",
        "DimensionName",
        "AllocationAsOfDate",
        "CoverageStatus",
        "ProviderName",
        "SourceDocumentId",
        "SourceLocator",
        "Url",
    ]
    parts = [
        entity(
            "AllocationSnapshot",
            "s",
            {
                "Id": "SnapshotId",
                "ETFId": "_etf",
                "AllocationDimensionId": "_dim",
                "SourceDocumentId": "_source",
                "AllocationAsOfDate": "AllocationAsOfDate",
                "CoverageStatus": "CoverageStatus",
                "SourceLocator": "SourceLocator",
            },
        ),
        entity(
            "ETF",
            "_etf",
            {"Id": "ETFId", "FundName": "FundName", "ETFProviderId": "_provider"},
        ),
        entity(
            "AllocationDimension",
            "_dim",
            {"Id": "_dimensionId", "DimensionName": "DimensionName"},
        ),
        entity("SourceDocument", "_source", {"Id": "SourceDocumentId", "Url": "Url"}),
        entity("ETFProvider", "_provider", {"LegalName": "ProviderName"}),
        ticker_pattern(),
    ]
    filters = []
    if etf_id is not None:
        filters.append(id_filter("ETFId", etf_id))
    if allocation_dimension_id is not None:
        filters.append(id_filter("_dimensionId", allocation_dimension_id))
    if dimension_name:
        filters.append(text_filter("DimensionName", dimension_name))
    if as_of_date:
        filters.append(text_filter("AllocationAsOfDate", as_of_date))
    if ticker:
        filters.append(
            f'FILTER EXISTS {{ ?i <{NS}identifiesETF> ?_etf; <{NS}identifierScheme> "Ticker"; <{NS}identifierValue> {Literal(str(ticker))} }}'
        )
    return query(
        db,
        cols,
        parts,
        "\n".join(filters),
        "ORDER BY ?AllocationAsOfDate ?Ticker ?SnapshotId",
    )


def get_allocation_entries(db, snapshot_id):
    cols = [
        "EntryId",
        "WeightFraction",
        "Label",
        "ContextKey",
        "CategoryCode",
        "AllocationCategoryId",
        "ClassificationSchemeId",
        "SchemeAuthority",
        "SchemeName",
        "Version",
        "DefinitionUrl",
    ]
    parts = [
        entity(
            "AllocationEntry",
            "entry",
            {
                "Id": "EntryId",
                "AllocationSnapshotId": "_snapshot",
                "WeightFraction": "WeightFraction",
                "AllocationCategoryId": "_category",
            },
        ),
        entity("AllocationSnapshot", "_snapshot", {"Id": "_snapshotId"}),
        entity(
            "AllocationCategory",
            "_category",
            {
                "Id": "AllocationCategoryId",
                "Label": "Label",
                "ContextKey": "ContextKey",
                "Code": "CategoryCode",
            },
        ),
    ]
    scheme = entity(
        "ClassificationScheme",
        "_scheme",
        {
            "Id": "ClassificationSchemeId",
            "SchemeAuthority": "SchemeAuthority",
            "SchemeName": "SchemeName",
            "Version": "Version",
            "DefinitionUrl": "DefinitionUrl",
        },
    )
    parts.append(f"OPTIONAL {{ ?_category <{NS}definedBy> ?_scheme . {scheme} }}")
    return query(
        db,
        cols,
        parts,
        id_filter("_snapshotId", snapshot_id),
        "ORDER BY DESC(?WeightFraction) ?Label ?EntryId",
    )


def get_disclosure_detail(db, snapshot_id):
    cols = [
        "SnapshotId",
        "AllocationAsOfDate",
        "BasisNote",
        "CoverageStatus",
        "SourceLocator",
        "ETFId",
        "FundName",
        "DimensionName",
        "SourceDocumentId",
        "PublisherId",
        "PublisherName",
        "Url",
        "CapturedFileRef",
        "RetrievedAt",
        "PublishedAt",
        "DocumentTitle",
    ]
    parts = [
        entity(
            "AllocationSnapshot",
            "s",
            {
                "Id": "SnapshotId",
                "AllocationAsOfDate": "AllocationAsOfDate",
                "BasisNote": "BasisNote",
                "CoverageStatus": "CoverageStatus",
                "SourceLocator": "SourceLocator",
                "ETFId": "_etf",
                "AllocationDimensionId": "_dim",
                "SourceDocumentId": "_source",
            },
        ),
        entity("ETF", "_etf", {"Id": "ETFId", "FundName": "FundName"}),
        entity("AllocationDimension", "_dim", {"DimensionName": "DimensionName"}),
        entity(
            "SourceDocument",
            "_source",
            {
                "Id": "SourceDocumentId",
                "ETFProviderId": "_publisher",
                "Url": "Url",
                "CapturedFileRef": "CapturedFileRef",
                "RetrievedAt": "RetrievedAt",
                "PublishedAt": "PublishedAt",
                "DocumentTitle": "DocumentTitle",
            },
        ),
        entity(
            "ETFProvider",
            "_publisher",
            {"Id": "PublisherId", "LegalName": "PublisherName"},
        ),
    ]
    rows = query(db, cols, parts, id_filter("SnapshotId", snapshot_id))
    if not rows:
        raise NotFoundError(f"Disclosure {snapshot_id} not found.")
    result = rows[0]
    result["Entries"] = get_allocation_entries(db, snapshot_id)
    return result


def get_customer_portfolio(
    db, customer_number, *, portfolio_id=None, holding_as_of_date=None
):
    rows = query(
        db,
        ["Id", "CustomerNumber", "GivenName", "FamilyName", "Email"],
        [
            entity(
                "Customer",
                "customer",
                {
                    k: k
                    for k in [
                        "Id",
                        "CustomerNumber",
                        "GivenName",
                        "FamilyName",
                        "Email",
                    ]
                },
            )
        ],
        text_filter("CustomerNumber", customer_number),
    )
    if not rows:
        raise NotFoundError(f"Customer {customer_number} not found.")
    result = rows[0]
    portfolios = query(
        db,
        ["Id", "PortfolioReference", "PortfolioName", "BaseCurrency"],
        [
            entity(
                "Portfolio",
                "p",
                {
                    "Id": "Id",
                    "CustomerId": "_customer",
                    "PortfolioReference": "PortfolioReference",
                    "PortfolioName": "PortfolioName",
                    "BaseCurrency": "BaseCurrency",
                },
            ),
            entity("Customer", "_customer", {"Id": "_customerId"}),
        ],
        id_filter("_customerId", result["Id"]),
    )
    if not portfolios:
        raise BusinessRuleError(f"Customer {customer_number} has no portfolio.")
    if portfolio_id is None:
        if len(portfolios) > 1:
            raise ValidationError("Choose a portfolio using portfolio_id.")
        portfolio = portfolios[0]
    else:
        portfolio = next((p for p in portfolios if p["Id"] == portfolio_id), None)
        if portfolio is None:
            raise NotFoundError(
                f"Portfolio {portfolio_id} does not belong to this customer."
            )
    holdings = query(
        db,
        [
            "HoldingId",
            "ETFId",
            "WeightFraction",
            "HoldingAsOfDate",
            "Ticker",
            "FundName",
        ],
        [
            entity(
                "Holding",
                "h",
                {
                    "Id": "HoldingId",
                    "ETFId": "_etf",
                    "PortfolioId": "_portfolio",
                    "WeightFraction": "WeightFraction",
                    "HoldingAsOfDate": "HoldingAsOfDate",
                },
            ),
            entity("Portfolio", "_portfolio", {"Id": "_portfolioId"}),
            entity("ETF", "_etf", {"Id": "ETFId", "FundName": "FundName"}),
            ticker_pattern(),
        ],
        id_filter("_portfolioId", portfolio["Id"]),
        "ORDER BY DESC(?WeightFraction) ?HoldingId",
    )
    if holding_as_of_date is None:
        dates = {h["HoldingAsOfDate"] for h in holdings}
        if len(dates) > 1:
            raise ValidationError("Choose a holding date using holding_as_of_date.")
        holding_as_of_date = next(iter(dates), None)
    result.update(
        Portfolio=portfolio,
        HoldingAsOfDate=holding_as_of_date,
        Holdings=[h for h in holdings if h["HoldingAsOfDate"] == holding_as_of_date],
    )
    return result


def next_id(candidate, table):
    answer = select(
        candidate,
        f"SELECT (COALESCE(MAX(?Id),0)+1 AS ?Next) WHERE {{ GRAPH {DATA_GRAPH} {{ ?s a <{NS}{table}>; <{NS}recordId> ?Id }} }}",
    )
    return int(answer[0]["Next"])


def create_disclosure(db, payload):
    if not payload.get("Entries"):
        raise BusinessRuleError("A saved disclosure must contain at least one entry.")

    def operation(candidate):
        sid = next_id(candidate, "AllocationSnapshot")
        eid = next_id(candidate, "AllocationEntry")
        fields = [
            "ETFId",
            "AllocationDimensionId",
            "SourceDocumentId",
            "AllocationAsOfDate",
            "BasisNote",
            "SourceLocator",
        ]
        try:
            row = {k: payload[k] for k in fields}
        except KeyError as exc:
            raise ValidationError(f"Missing field {exc.args[0]}") from exc
        row.update(Id=sid, CoverageStatus=payload.get("CoverageStatus", "Complete"))
        quads = list(record_quads("AllocationSnapshot", row))
        for offset, item in enumerate(payload["Entries"]):
            if "AllocationCategoryId" not in item:
                raise ValidationError("Category ID is required.")
            quads.extend(
                record_quads(
                    "AllocationEntry",
                    {
                        "Id": eid + offset,
                        "AllocationSnapshotId": sid,
                        "AllocationCategoryId": item["AllocationCategoryId"],
                        "WeightFraction": _validate_weight(item.get("WeightFraction")),
                    },
                )
            )
        candidate.update("INSERT DATA { " + block(quads) + " }")
        return sid

    try:
        sid = db.mutate(operation)
    except ModelIntegrityError as exc:
        raise BusinessRuleError(str(exc)) from exc
    return get_disclosure_detail(db, sid)


def entry_row(db, entry_id, include_category=False):
    columns = ["EntryId", "AllocationSnapshotId", "WeightFraction", "Label"]
    if include_category:
        columns.append("AllocationCategoryId")
    rows = query(
        db,
        columns,
        [
            entity(
                "AllocationEntry",
                "e",
                {
                    "Id": "EntryId",
                    "AllocationSnapshotId": "_s",
                    "AllocationCategoryId": "_c",
                    "WeightFraction": "WeightFraction",
                },
            ),
            entity("AllocationSnapshot", "_s", {"Id": "AllocationSnapshotId"}),
            entity(
                "AllocationCategory",
                "_c",
                {"Id": "AllocationCategoryId", "Label": "Label"},
            ),
        ],
        id_filter("EntryId", entry_id),
    )
    if not rows:
        raise NotFoundError(f"Entry {entry_id} not found.")
    return rows[0]


def update_weights_batch(db, changes):
    if not changes:
        raise ValidationError("No changes supplied.")
    normalized = [
        (c["EntryId"], _validate_weight(c.get("WeightFraction"))) for c in changes
    ]
    if len({i for i, w in normalized}) != len(normalized):
        raise ValidationError("Duplicate entry ID.")

    def operation(candidate):
        for i, weight in normalized:
            entry_row(candidate, i)
            subject = resource("AllocationEntry", i)
            pred = predicate("AllocationEntry", "WeightFraction")
            term = Literal(str(weight), datatype=NamedNode(XSD + "double"))
            candidate.update(
                f"DELETE {{ GRAPH {DATA_GRAPH} {{ {subject} {pred} ?old }} }} INSERT {{ GRAPH {DATA_GRAPH} {{ {subject} {pred} {term} }} }} WHERE {{ GRAPH {DATA_GRAPH} {{ {subject} {pred} ?old }} }}"
            )

    try:
        db.mutate(operation)
    except ModelIntegrityError as exc:
        raise BusinessRuleError(str(exc)) from exc
    return [entry_row(db, i) for i, w in normalized]


def update_entry_weight(db, entry_id, new_weight):
    update_weights_batch(db, [{"EntryId": entry_id, "WeightFraction": new_weight}])
    return entry_row(db, entry_id, True)


def delete_entry(db, entry_id):
    def operation(candidate):
        existing = entry_row(candidate, entry_id)
        candidate.update(
            f"DELETE WHERE {{ GRAPH {DATA_GRAPH} {{ {resource('AllocationEntry', entry_id)} ?p ?o }} }}"
        )
        return {
            "DeletedEntryId": entry_id,
            "AllocationSnapshotId": existing["AllocationSnapshotId"],
        }

    try:
        return db.mutate(operation)
    except ModelIntegrityError as exc:
        raise BusinessRuleError(str(exc)) from exc
