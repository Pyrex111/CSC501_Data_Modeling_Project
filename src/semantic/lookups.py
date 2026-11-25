"""SPARQL equivalents of all seven M4 form lookup functions."""

from .repositories import entity, id_filter, query, text_filter, ticker_pattern


def list_etfs(db):
    return query(
        db,
        ["ETFId", "FundName", "Ticker"],
        [
            entity("ETF", "_etf", {"Id": "ETFId", "FundName": "FundName"}),
            ticker_pattern(),
        ],
        order="ORDER BY ?Ticker ?ETFId",
    )


def list_dimensions(db):
    return query(
        db,
        ["DimensionId", "DimensionName"],
        [
            entity(
                "AllocationDimension",
                "d",
                {"Id": "DimensionId", "DimensionName": "DimensionName"},
            )
        ],
        order="ORDER BY ?DimensionId",
    )


def list_source_documents(db):
    return query(
        db,
        ["SourceDocumentId", "DocumentTitle", "Url", "RetrievedAt", "ProviderName"],
        [
            entity(
                "SourceDocument",
                "s",
                {
                    "Id": "SourceDocumentId",
                    "DocumentTitle": "DocumentTitle",
                    "Url": "Url",
                    "RetrievedAt": "RetrievedAt",
                    "ETFProviderId": "_provider",
                },
            ),
            entity("ETFProvider", "_provider", {"LegalName": "ProviderName"}),
        ],
        order="ORDER BY ?SourceDocumentId",
    )


def list_categories(db):
    from .vocabulary import NS

    return query(
        db,
        [
            "CategoryId",
            "AllocationDimensionId",
            "Label",
            "Code",
            "ContextKey",
            "SchemeName",
            "Version",
        ],
        [
            entity(
                "AllocationCategory",
                "c",
                {
                    "Id": "CategoryId",
                    "AllocationDimensionId": "_dim",
                    "Label": "Label",
                    "Code": "Code",
                    "ContextKey": "ContextKey",
                },
            ),
            entity("AllocationDimension", "_dim", {"Id": "AllocationDimensionId"}),
            "OPTIONAL { ?c <"
            + NS
            + "definedBy> ?scheme . "
            + entity(
                "ClassificationScheme",
                "scheme",
                {"SchemeName": "SchemeName", "Version": "Version"},
            )
            + " }",
        ],
        order="ORDER BY ?AllocationDimensionId ?Label ?CategoryId",
    )


def list_customers(db):
    return query(
        db,
        ["CustomerNumber", "GivenName", "FamilyName"],
        [
            entity(
                "Customer",
                "c",
                {k: k for k in ["CustomerNumber", "GivenName", "FamilyName"]},
            )
        ],
        order="ORDER BY ?CustomerNumber",
    )


def list_customer_portfolios(db, customer_number):
    return query(
        db,
        ["PortfolioId", "PortfolioReference", "PortfolioName"],
        [
            entity(
                "Portfolio",
                "p",
                {
                    "Id": "PortfolioId",
                    "PortfolioReference": "PortfolioReference",
                    "PortfolioName": "PortfolioName",
                    "CustomerId": "_customer",
                },
            ),
            entity("Customer", "_customer", {"CustomerNumber": "CustomerNumber"}),
        ],
        text_filter("CustomerNumber", customer_number),
        "ORDER BY ?PortfolioReference",
    )


def list_holding_dates(db, portfolio_id):
    rows = query(
        db,
        ["HoldingAsOfDate"],
        [
            entity(
                "Holding",
                "h",
                {"PortfolioId": "_portfolio", "HoldingAsOfDate": "HoldingAsOfDate"},
            ),
            entity("Portfolio", "_portfolio", {"Id": "PortfolioId"}),
        ],
        id_filter("PortfolioId", portfolio_id),
    )
    return sorted({r["HoldingAsOfDate"] for r in rows}, reverse=True)
