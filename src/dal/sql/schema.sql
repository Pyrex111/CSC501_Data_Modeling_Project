-- CSC501 Milestone 4: relational mapping of the revised conceptual ERD.
-- Owner: Taimoor Shahzad. Prepared with AI assistance; see contribution notes.
-- SQLite >= 3.37.0 (STRICT tables). Run once on a fresh database.
-- This script creates the schema only. Seed data and application DML are separate.
-- Every application connection must enable foreign_keys before BEGIN.
PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE Customer (
    Id INTEGER CONSTRAINT PK_Customer PRIMARY KEY,
    CustomerNumber TEXT NOT NULL,
    GivenName TEXT NOT NULL,
    FamilyName TEXT NOT NULL,
    Email TEXT,
    CONSTRAINT UK_Customer_CustomerNumber UNIQUE (CustomerNumber),
    CONSTRAINT CK_Customer_CustomerNumber CHECK (
        LENGTH(TRIM(CustomerNumber)) > 0 AND CustomerNumber = TRIM(CustomerNumber)
    ),
    CONSTRAINT CK_Customer_GivenName CHECK (LENGTH(TRIM(GivenName)) > 0),
    CONSTRAINT CK_Customer_FamilyName CHECK (LENGTH(TRIM(FamilyName)) > 0),
    CONSTRAINT CK_Customer_Email CHECK (Email IS NULL OR LENGTH(TRIM(Email)) > 0)
) STRICT;

CREATE TABLE ETFProvider (
    Id INTEGER CONSTRAINT PK_ETFProvider PRIMARY KEY,
    LegalName TEXT NOT NULL,
    RegistrationNumber TEXT NOT NULL,
    RegistrationJurisdiction TEXT NOT NULL,
    WebsiteUrl TEXT,
    CONSTRAINT UK_ETFProvider_Registration UNIQUE (
        RegistrationJurisdiction, RegistrationNumber
    ),
    CONSTRAINT CK_ETFProvider_LegalName CHECK (LENGTH(TRIM(LegalName)) > 0),
    CONSTRAINT CK_ETFProvider_RegistrationNumber CHECK (
        LENGTH(TRIM(RegistrationNumber)) > 0
        AND RegistrationNumber = TRIM(RegistrationNumber)
    ),
    CONSTRAINT CK_ETFProvider_RegistrationJurisdiction CHECK (
        LENGTH(TRIM(RegistrationJurisdiction)) > 0
        AND RegistrationJurisdiction = TRIM(RegistrationJurisdiction)
    ),
    CONSTRAINT CK_ETFProvider_WebsiteUrl CHECK (
        WebsiteUrl IS NULL OR LENGTH(TRIM(WebsiteUrl)) > 0
    )
) STRICT;

CREATE TABLE AllocationDimension (
    Id INTEGER CONSTRAINT PK_AllocationDimension PRIMARY KEY,
    DimensionName TEXT NOT NULL,
    CONSTRAINT UK_AllocationDimension_DimensionName UNIQUE (DimensionName),
    CONSTRAINT CK_AllocationDimension_DimensionName CHECK (
        DimensionName IN ('Sector', 'Geography')
    )
) STRICT;

CREATE TABLE ClassificationScheme (
    Id INTEGER CONSTRAINT PK_ClassificationScheme PRIMARY KEY,
    SchemeAuthority TEXT NOT NULL,
    SchemeName TEXT NOT NULL,
    Version TEXT,
    DefinitionUrl TEXT,
    CONSTRAINT CK_ClassificationScheme_SchemeAuthority CHECK (
        LENGTH(TRIM(SchemeAuthority)) > 0 AND SchemeAuthority = TRIM(SchemeAuthority)
    ),
    CONSTRAINT CK_ClassificationScheme_SchemeName CHECK (
        LENGTH(TRIM(SchemeName)) > 0 AND SchemeName = TRIM(SchemeName)
    ),
    CONSTRAINT CK_ClassificationScheme_Version CHECK (
        Version IS NULL OR (LENGTH(TRIM(Version)) > 0 AND Version = TRIM(Version))
    ),
    CONSTRAINT CK_ClassificationScheme_DefinitionUrl CHECK (
        DefinitionUrl IS NULL OR LENGTH(TRIM(DefinitionUrl)) > 0
    )
) STRICT;

-- A version-dependent identifier is not a candidate key when Version is NULL.
-- Unresolved records remain distinct; do not coalesce NULL to a fictional version.
CREATE UNIQUE INDEX UK_ClassificationScheme_KnownVersion
    ON ClassificationScheme (SchemeAuthority, SchemeName, Version)
    WHERE Version IS NOT NULL;

CREATE TABLE Portfolio (
    Id INTEGER CONSTRAINT PK_Portfolio PRIMARY KEY,
    CustomerId INTEGER NOT NULL,
    PortfolioReference TEXT NOT NULL,
    PortfolioName TEXT NOT NULL,
    BaseCurrency TEXT NOT NULL,
    CONSTRAINT UK_Portfolio_CustomerReference UNIQUE (CustomerId, PortfolioReference),
    CONSTRAINT FK_Portfolio_CustomerId_2_Customer_Id
        FOREIGN KEY (CustomerId) REFERENCES Customer (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_Portfolio_PortfolioReference CHECK (
        LENGTH(TRIM(PortfolioReference)) > 0 AND PortfolioReference = TRIM(PortfolioReference)
    ),
    CONSTRAINT CK_Portfolio_PortfolioName CHECK (LENGTH(TRIM(PortfolioName)) > 0),
    CONSTRAINT CK_Portfolio_BaseCurrency CHECK (BaseCurrency GLOB '[A-Z][A-Z][A-Z]')
) STRICT;

CREATE TABLE ETF (
    Id INTEGER CONSTRAINT PK_ETF PRIMARY KEY,
    ETFProviderId INTEGER NOT NULL,
    FundName TEXT NOT NULL,
    DomicileCountryCode TEXT NOT NULL,
    BaseCurrency TEXT NOT NULL,
    InceptionDate TEXT,
    CONSTRAINT FK_ETF_ETFProviderId_2_ETFProvider_Id
        FOREIGN KEY (ETFProviderId) REFERENCES ETFProvider (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_ETF_FundName CHECK (LENGTH(TRIM(FundName)) > 0),
    CONSTRAINT CK_ETF_DomicileCountryCode CHECK (DomicileCountryCode GLOB '[A-Z][A-Z]'),
    CONSTRAINT CK_ETF_BaseCurrency CHECK (BaseCurrency GLOB '[A-Z][A-Z][A-Z]'),
    CONSTRAINT CK_ETF_InceptionDate CHECK (
        InceptionDate IS NULL OR (
            LENGTH(InceptionDate) = 10
            AND InceptionDate GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
            AND DATE(InceptionDate, '+0 days') IS NOT NULL
            AND DATE(InceptionDate, '+0 days') = InceptionDate
        )
    )
) STRICT;

CREATE TABLE ETFIdentifier (
    Id INTEGER CONSTRAINT PK_ETFIdentifier PRIMARY KEY,
    ETFId INTEGER NOT NULL,
    IdentifierScheme TEXT NOT NULL,
    IdentifierValue TEXT NOT NULL,
    ExchangeContext TEXT,
    CONSTRAINT FK_ETFIdentifier_ETFId_2_ETF_Id
        FOREIGN KEY (ETFId) REFERENCES ETF (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_ETFIdentifier_Scheme CHECK (IdentifierScheme IN ('ISIN', 'Ticker')),
    CONSTRAINT CK_ETFIdentifier_Value CHECK (
        LENGTH(TRIM(IdentifierValue)) > 0 AND IdentifierValue = TRIM(IdentifierValue)
        AND IdentifierValue = UPPER(IdentifierValue)
    ),
    CONSTRAINT CK_ETFIdentifier_Context CHECK (
        (IdentifierScheme = 'ISIN' AND ExchangeContext IS NULL
            AND LENGTH(IdentifierValue) = 12
            AND SUBSTR(IdentifierValue, 1, 2) GLOB '[A-Z][A-Z]'
            AND IdentifierValue NOT GLOB '*[^A-Z0-9]*'
            AND SUBSTR(IdentifierValue, 12, 1) GLOB '[0-9]')
        OR
        (IdentifierScheme = 'Ticker' AND ExchangeContext IS NOT NULL
            AND LENGTH(TRIM(ExchangeContext)) > 0
            AND ExchangeContext = TRIM(ExchangeContext)
            AND ExchangeContext = UPPER(ExchangeContext))
    )
) STRICT;

CREATE UNIQUE INDEX UK_ETFIdentifier_ISIN
    ON ETFIdentifier (IdentifierScheme, IdentifierValue)
    WHERE IdentifierScheme = 'ISIN';

CREATE UNIQUE INDEX UK_ETFIdentifier_TickerExchange
    ON ETFIdentifier (IdentifierScheme, IdentifierValue, ExchangeContext)
    WHERE IdentifierScheme = 'Ticker';

CREATE INDEX IX_ETFIdentifier_ETFId ON ETFIdentifier (ETFId);
CREATE INDEX IX_ETF_ETFProviderId ON ETF (ETFProviderId);

CREATE TABLE Holding (
    Id INTEGER CONSTRAINT PK_Holding PRIMARY KEY,
    PortfolioId INTEGER NOT NULL,
    ETFId INTEGER NOT NULL,
    WeightFraction REAL NOT NULL,
    HoldingAsOfDate TEXT NOT NULL,
    CONSTRAINT UK_Holding_PortfolioETFDate UNIQUE (PortfolioId, ETFId, HoldingAsOfDate),
    CONSTRAINT FK_Holding_PortfolioId_2_Portfolio_Id
        FOREIGN KEY (PortfolioId) REFERENCES Portfolio (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT FK_Holding_ETFId_2_ETF_Id
        FOREIGN KEY (ETFId) REFERENCES ETF (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_Holding_WeightFraction CHECK (WeightFraction BETWEEN 0.0 AND 1.0),
    CONSTRAINT CK_Holding_AsOfDate CHECK (
        LENGTH(HoldingAsOfDate) = 10
        AND HoldingAsOfDate GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND DATE(HoldingAsOfDate, '+0 days') IS NOT NULL
        AND DATE(HoldingAsOfDate, '+0 days') = HoldingAsOfDate
    )
) STRICT;

CREATE INDEX IX_Holding_ETFId ON Holding (ETFId);

CREATE TABLE SourceDocument (
    Id INTEGER CONSTRAINT PK_SourceDocument PRIMARY KEY,
    ETFProviderId INTEGER NOT NULL,
    Url TEXT NOT NULL,
    RetrievedAt TEXT NOT NULL,
    PublishedAt TEXT,
    CapturedFileRef TEXT NOT NULL,
    DocumentTitle TEXT,
    CONSTRAINT UK_SourceDocument_UrlRetrievedAt UNIQUE (Url, RetrievedAt),
    CONSTRAINT FK_SourceDocument_ETFProviderId_2_ETFProvider_Id
        FOREIGN KEY (ETFProviderId) REFERENCES ETFProvider (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_SourceDocument_Url CHECK (
        LENGTH(TRIM(Url)) > 0 AND Url = TRIM(Url)
    ),
    CONSTRAINT CK_SourceDocument_RetrievedAt CHECK (
        LENGTH(RetrievedAt) = 27 AND SUBSTR(RetrievedAt, 20, 1) = '.'
        AND SUBSTR(RetrievedAt, 27, 1) = 'Z'
        AND SUBSTR(RetrievedAt, 21, 6) NOT GLOB '*[^0-9]*'
        AND STRFTIME('%Y-%m-%dT%H:%M:%S', SUBSTR(RetrievedAt, 1, 19), '+0 seconds') IS NOT NULL
        AND STRFTIME('%Y-%m-%dT%H:%M:%S', SUBSTR(RetrievedAt, 1, 19), '+0 seconds')
            = SUBSTR(RetrievedAt, 1, 19)
    ),
    CONSTRAINT CK_SourceDocument_PublishedAt CHECK (
        PublishedAt IS NULL OR (
            LENGTH(PublishedAt) = 27 AND SUBSTR(PublishedAt, 20, 1) = '.'
            AND SUBSTR(PublishedAt, 27, 1) = 'Z'
            AND SUBSTR(PublishedAt, 21, 6) NOT GLOB '*[^0-9]*'
            AND STRFTIME('%Y-%m-%dT%H:%M:%S', SUBSTR(PublishedAt, 1, 19), '+0 seconds') IS NOT NULL
            AND STRFTIME('%Y-%m-%dT%H:%M:%S', SUBSTR(PublishedAt, 1, 19), '+0 seconds')
                = SUBSTR(PublishedAt, 1, 19)
        )
    ),
    CONSTRAINT CK_SourceDocument_CapturedFileRef CHECK (
        LENGTH(TRIM(CapturedFileRef)) > 0 AND CapturedFileRef = TRIM(CapturedFileRef)
    ),
    CONSTRAINT CK_SourceDocument_DocumentTitle CHECK (
        DocumentTitle IS NULL OR LENGTH(TRIM(DocumentTitle)) > 0
    )
) STRICT;

CREATE INDEX IX_SourceDocument_ETFProviderId ON SourceDocument (ETFProviderId);

CREATE TABLE AllocationCategory (
    Id INTEGER CONSTRAINT PK_AllocationCategory PRIMARY KEY,
    AllocationDimensionId INTEGER NOT NULL,
    ClassificationSchemeId INTEGER,
    Label TEXT NOT NULL,
    Code TEXT,
    ContextKey TEXT NOT NULL,
    CONSTRAINT UK_AllocationCategory_ContextLabel UNIQUE (
        AllocationDimensionId, ContextKey, Label
    ),
    CONSTRAINT FK_AllocationCategory_AllocationDimensionId_2_AllocationDimension_Id
        FOREIGN KEY (AllocationDimensionId) REFERENCES AllocationDimension (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT FK_AllocationCategory_ClassificationSchemeId_2_ClassificationScheme_Id
        FOREIGN KEY (ClassificationSchemeId) REFERENCES ClassificationScheme (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_AllocationCategory_Label CHECK (
        LENGTH(TRIM(Label)) > 0 AND Label = TRIM(Label)
    ),
    CONSTRAINT CK_AllocationCategory_Code CHECK (Code IS NULL OR LENGTH(TRIM(Code)) > 0),
    CONSTRAINT CK_AllocationCategory_ContextKey CHECK (
        LENGTH(TRIM(ContextKey)) > 0 AND ContextKey = TRIM(ContextKey)
    )
) STRICT;

CREATE INDEX IX_AllocationCategory_ClassificationSchemeId
    ON AllocationCategory (ClassificationSchemeId);

CREATE TABLE AllocationSnapshot (
    Id INTEGER CONSTRAINT PK_AllocationSnapshot PRIMARY KEY,
    ETFId INTEGER NOT NULL,
    AllocationDimensionId INTEGER NOT NULL,
    SourceDocumentId INTEGER NOT NULL,
    AllocationAsOfDate TEXT NOT NULL,
    BasisNote TEXT NOT NULL,
    CoverageStatus TEXT NOT NULL,
    SourceLocator TEXT NOT NULL,
    CONSTRAINT UK_AllocationSnapshot_DisclosureBlock UNIQUE (
        ETFId, AllocationDimensionId, AllocationAsOfDate, SourceDocumentId, SourceLocator
    ),
    CONSTRAINT FK_AllocationSnapshot_ETFId_2_ETF_Id
        FOREIGN KEY (ETFId) REFERENCES ETF (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT FK_AllocationSnapshot_AllocationDimensionId_2_AllocationDimension_Id
        FOREIGN KEY (AllocationDimensionId) REFERENCES AllocationDimension (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT FK_AllocationSnapshot_SourceDocumentId_2_SourceDocument_Id
        FOREIGN KEY (SourceDocumentId) REFERENCES SourceDocument (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_AllocationSnapshot_AsOfDate CHECK (
        LENGTH(AllocationAsOfDate) = 10
        AND AllocationAsOfDate GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND DATE(AllocationAsOfDate, '+0 days') IS NOT NULL
        AND DATE(AllocationAsOfDate, '+0 days') = AllocationAsOfDate
    ),
    CONSTRAINT CK_AllocationSnapshot_BasisNote CHECK (LENGTH(TRIM(BasisNote)) > 0),
    CONSTRAINT CK_AllocationSnapshot_CoverageStatus CHECK (
        CoverageStatus IN ('Complete', 'Partial', 'Unknown')
    ),
    CONSTRAINT CK_AllocationSnapshot_SourceLocator CHECK (
        LENGTH(TRIM(SourceLocator)) > 0 AND SourceLocator = TRIM(SourceLocator)
    )
) STRICT;

CREATE INDEX IX_AllocationSnapshot_DimensionDate
    ON AllocationSnapshot (AllocationDimensionId, AllocationAsOfDate);
CREATE INDEX IX_AllocationSnapshot_SourceDocumentId ON AllocationSnapshot (SourceDocumentId);

CREATE TABLE AllocationEntry (
    Id INTEGER CONSTRAINT PK_AllocationEntry PRIMARY KEY,
    AllocationSnapshotId INTEGER NOT NULL,
    AllocationCategoryId INTEGER NOT NULL,
    WeightFraction REAL NOT NULL,
    CONSTRAINT UK_AllocationEntry_SnapshotCategory UNIQUE (
        AllocationSnapshotId, AllocationCategoryId
    ),
    CONSTRAINT FK_AllocationEntry_AllocationSnapshotId_2_AllocationSnapshot_Id
        FOREIGN KEY (AllocationSnapshotId) REFERENCES AllocationSnapshot (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT FK_AllocationEntry_AllocationCategoryId_2_AllocationCategory_Id
        FOREIGN KEY (AllocationCategoryId) REFERENCES AllocationCategory (Id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT CK_AllocationEntry_WeightFraction CHECK (WeightFraction BETWEEN 0.0 AND 1.0)
) STRICT;

CREATE INDEX IX_AllocationEntry_AllocationCategoryId ON AllocationEntry (AllocationCategoryId);

-- Protect the dimension invariant for entry writes AND later parent edits.
CREATE TRIGGER TR_AllocationEntry_Dimension_Insert
BEFORE INSERT ON AllocationEntry
WHEN (SELECT AllocationDimensionId FROM AllocationSnapshot WHERE Id = NEW.AllocationSnapshotId)
    <> (SELECT AllocationDimensionId FROM AllocationCategory WHERE Id = NEW.AllocationCategoryId)
BEGIN
    SELECT RAISE(ABORT, 'Category and snapshot dimensions must agree');
END;

CREATE TRIGGER TR_AllocationEntry_Dimension_Update
BEFORE UPDATE OF AllocationSnapshotId, AllocationCategoryId ON AllocationEntry
WHEN (SELECT AllocationDimensionId FROM AllocationSnapshot WHERE Id = NEW.AllocationSnapshotId)
    <> (SELECT AllocationDimensionId FROM AllocationCategory WHERE Id = NEW.AllocationCategoryId)
BEGIN
    SELECT RAISE(ABORT, 'Category and snapshot dimensions must agree');
END;

CREATE TRIGGER TR_AllocationSnapshot_Dimension_Update
BEFORE UPDATE OF AllocationDimensionId ON AllocationSnapshot
WHEN EXISTS (
    SELECT 1 FROM AllocationEntry AS E
    JOIN AllocationCategory AS C ON C.Id = E.AllocationCategoryId
    WHERE E.AllocationSnapshotId = OLD.Id AND C.AllocationDimensionId <> NEW.AllocationDimensionId
)
BEGIN
    SELECT RAISE(ABORT, 'Snapshot dimension conflicts with existing entries');
END;

CREATE TRIGGER TR_AllocationCategory_Dimension_Update
BEFORE UPDATE OF AllocationDimensionId ON AllocationCategory
WHEN EXISTS (
    SELECT 1 FROM AllocationEntry AS E
    JOIN AllocationSnapshot AS S ON S.Id = E.AllocationSnapshotId
    WHERE E.AllocationCategoryId = OLD.Id AND S.AllocationDimensionId <> NEW.AllocationDimensionId
)
BEGIN
    SELECT RAISE(ABORT, 'Category dimension conflicts with existing entries');
END;

-- Parent-side minimum participation, contextual identity and complete totals are
-- checked before COMMIT by src/dal/schema_validation.py. Ordinary FKs do not
-- require an ETF to have an identifier or a snapshot to have an entry.
COMMIT;
