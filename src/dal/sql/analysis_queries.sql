-- CSC501 Milestone 4 - analytical SELECT/JOIN/aggregate queries.
-- All queries keep observation date, dimension and classification context.
-- Weights are synthetic; identifiers and dates are real and sourced.

-- Q1. Geographic exposure across issuers, with observation date.
-- VFV/VUN are observed 2026-05-31, XIC 2026-06-30: not directly summable.
SELECT t.IdentifierValue AS Ticker,
       p.LegalName       AS Provider,
       c.Label           AS Region,
       c.ContextKey,
       e.WeightFraction,
       s.AllocationAsOfDate,
       d.RetrievedAt
FROM AllocationEntry e
JOIN AllocationSnapshot  s   ON s.Id = e.AllocationSnapshotId
JOIN AllocationCategory  c   ON c.Id = e.AllocationCategoryId
JOIN AllocationDimension dim ON dim.Id = s.AllocationDimensionId
JOIN ETF                  f   ON f.Id = s.ETFId
JOIN ETFIdentifier        t   ON t.ETFId = f.Id AND t.IdentifierScheme = 'Ticker'
JOIN ETFProvider          p   ON p.Id = f.ETFProviderId
JOIN SourceDocument       d   ON d.Id = s.SourceDocumentId
WHERE dim.DimensionName = 'Geography'
ORDER BY s.AllocationAsOfDate, Ticker, e.WeightFraction DESC;

-- Q2. Which ETFs have exposure to a specified sector (Financials)?
SELECT t.IdentifierValue AS Ticker,
       c.Label           AS Sector,
       e.WeightFraction,
       s.AllocationAsOfDate
FROM AllocationEntry e
JOIN AllocationSnapshot  s   ON s.Id = e.AllocationSnapshotId
JOIN AllocationCategory  c   ON c.Id = e.AllocationCategoryId
JOIN AllocationDimension dim ON dim.Id = s.AllocationDimensionId
JOIN ETF                 f   ON f.Id = s.ETFId
JOIN ETFIdentifier       t   ON t.ETFId = f.Id AND t.IdentifierScheme = 'Ticker'
WHERE dim.DimensionName = 'Sector'
  AND c.Label = 'Financials'
ORDER BY e.WeightFraction DESC;

-- Q3. Aggregate: number of categories and total weight per snapshot.
SELECT s.Id AS SnapshotId,
       dim.DimensionName,
       COUNT(e.Id) AS NumberOfCategories,
       ROUND(SUM(e.WeightFraction), 4) AS TotalWeight
FROM AllocationSnapshot s
JOIN AllocationDimension dim ON dim.Id = s.AllocationDimensionId
JOIN AllocationEntry     e   ON e.AllocationSnapshotId = s.Id
GROUP BY s.Id, dim.DimensionName
ORDER BY s.Id;

-- Q4. Observation vs publication/capture dates per snapshot.
SELECT t.IdentifierValue AS Ticker,
       dim.DimensionName,
       s.AllocationAsOfDate AS ObservationDate,
       d.PublishedAt,
       d.RetrievedAt
FROM AllocationSnapshot s
JOIN ETF                 f   ON f.Id = s.ETFId
JOIN ETFIdentifier       t   ON t.ETFId = f.Id AND t.IdentifierScheme = 'Ticker'
JOIN AllocationDimension dim ON dim.Id = s.AllocationDimensionId
JOIN SourceDocument      d   ON d.Id = s.SourceDocumentId
ORDER BY Ticker, dim.DimensionName;

-- Q5. Portfolio look-through to United States (holding * fund U.S. allocation).
-- Holding and observation dates are returned so compatibility is judged, not assumed.
SELECT port.PortfolioReference,
       t.IdentifierValue AS Ticker,
       h.WeightFraction AS HoldingWeight,
       geo.WeightFraction AS FundUSAllocation,
       ROUND(h.WeightFraction * geo.WeightFraction, 4) AS PortfolioUSExposure,
       h.HoldingAsOfDate,
       s.AllocationAsOfDate
FROM Holding h
JOIN Portfolio         port ON port.Id = h.PortfolioId
JOIN ETF               f    ON f.Id = h.ETFId
JOIN ETFIdentifier     t    ON t.ETFId = f.Id AND t.IdentifierScheme = 'Ticker'
JOIN AllocationSnapshot s   ON s.ETFId = f.Id
JOIN AllocationDimension dim ON dim.Id = s.AllocationDimensionId
                            AND dim.DimensionName = 'Geography'
JOIN AllocationEntry   geo  ON geo.AllocationSnapshotId = s.Id
JOIN AllocationCategory cat ON cat.Id = geo.AllocationCategoryId
                            AND cat.Label = 'United States'
ORDER BY port.PortfolioReference, Ticker;

-- Q6. Provenance trace: every entry back to its captured source.
SELECT e.Id AS EntryId,
       t.IdentifierValue AS Ticker,
       c.Label,
       e.WeightFraction,
       d.Url,
       d.CapturedFileRef
FROM AllocationEntry e
JOIN AllocationSnapshot s   ON s.Id = e.AllocationSnapshotId
JOIN AllocationCategory c   ON c.Id = e.AllocationCategoryId
JOIN ETF               f   ON f.Id = s.ETFId
JOIN ETFIdentifier     t   ON t.ETFId = f.Id AND t.IdentifierScheme = 'Ticker'
JOIN SourceDocument    d   ON d.Id = s.SourceDocumentId
ORDER BY Ticker, e.Id;
