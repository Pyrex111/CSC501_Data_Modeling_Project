-- CSC501 Milestone 4: demonstration seed data.
-- Owner: Mason Li. Run against a database that already has schema.sql applied.
-- The application loads this same dataset through src/dal/seed_data.py inside a
-- validated transaction; this file is the human-readable SQL reference.
--
-- Identifying facts (names, identifiers, dates, source URLs) are real and
-- traceable; ALL WeightFraction values are synthetic. Provider registration
-- numbers are labelled placeholders and must be replaced/verified.
PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- Customers ---------------------------------------------------------------
INSERT INTO Customer VALUES (1, '1001', 'Alice', 'Chen',
                             'alice.chen@example.invalid');
INSERT INTO Customer VALUES (2, '1002', 'Brian', 'Li', NULL);

-- Providers (registration numbers are placeholders) -----------------------
INSERT INTO ETFProvider VALUES (1, 'Vanguard Investments Canada Inc.',
                                'REG-PLACEHOLDER-VAN', 'CA-FEDERAL',
                                'https://www.vanguard.ca');
INSERT INTO ETFProvider VALUES (2, 'BlackRock Asset Management Canada Limited',
                                'REG-PLACEHOLDER-BLK', 'CA-FEDERAL',
                                'https://www.blackrock.com/ca');

-- Dimensions --------------------------------------------------------------
INSERT INTO AllocationDimension VALUES (1, 'Sector');
INSERT INTO AllocationDimension VALUES (2, 'Geography');

-- Classification schemes (one known version, one unknown) -----------------
INSERT INTO ClassificationScheme VALUES (1, 'S&P Dow Jones Indices',
                                         'GICS', '2025', NULL);
INSERT INTO ClassificationScheme VALUES (2, 'Vanguard Investments Canada',
                                         'Regional Classification', NULL, NULL);

-- Portfolios --------------------------------------------------------------
INSERT INTO Portfolio VALUES (1, 1, 'P-ALICE-01', 'Growth Portfolio', 'CAD');
INSERT INTO Portfolio VALUES (2, 2, 'P-BRIAN-01', 'Balanced Portfolio', 'CAD');

-- ETFs --------------------------------------------------------------------
INSERT INTO ETF VALUES (1, 1, 'Vanguard S&P 500 Index ETF',
                        'CA', 'CAD', NULL);
INSERT INTO ETF VALUES (2, 1, 'Vanguard U.S. Total Market Index ETF',
                        'CA', 'CAD', NULL);
INSERT INTO ETF VALUES (3, 2,
                        'iShares Core S&P/TSX Capped Composite Index ETF',
                        'CA', 'CAD', NULL);

-- Identifiers (ISIN + Ticker per ETF) -------------------------------------
INSERT INTO ETFIdentifier VALUES (1, 1, 'ISIN', 'CA9229081082', NULL);
INSERT INTO ETFIdentifier VALUES (2, 1, 'Ticker', 'VFV', 'XTSX');
INSERT INTO ETFIdentifier VALUES (3, 2, 'ISIN', 'CA9229071034', NULL);
INSERT INTO ETFIdentifier VALUES (4, 2, 'Ticker', 'VUN', 'XTSX');
INSERT INTO ETFIdentifier VALUES (5, 3, 'ISIN', 'CA46430J1005', NULL);
INSERT INTO ETFIdentifier VALUES (6, 3, 'Ticker', 'XIC', 'XTSX');

-- Holdings (synthetic portfolio weights) ----------------------------------
INSERT INTO Holding VALUES (1, 1, 1, 0.60, '2026-08-01');
INSERT INTO Holding VALUES (2, 1, 3, 0.40, '2026-08-01');
INSERT INTO Holding VALUES (3, 2, 1, 0.30, '2026-08-01');
INSERT INTO Holding VALUES (4, 2, 2, 0.20, '2026-08-01');
INSERT INTO Holding VALUES (5, 2, 3, 0.50, '2026-08-01');

-- Source documents (PublishedAt unknown -> NULL) --------------------------
INSERT INTO SourceDocument VALUES (
    1, 1,
    'https://www.vanguard.ca/en/product/etf/equity/9563/vanguard-sp-500-index-etf',
    '2026-09-23T09:15:00.000000Z', NULL,
    'data/raw/vanguard_vfv_etf_facts_20260716.pdf', 'Vanguard VFV ETF Facts');
INSERT INTO SourceDocument VALUES (
    2, 1,
    'https://www.vanguard.ca/en/product/etf/equity/9511/vanguard-us-total-market-index-etf',
    '2026-09-23T09:20:00.000000Z', NULL,
    'data/raw/vanguard_vun_etf_facts_20260716.pdf', 'Vanguard VUN ETF Facts');
INSERT INTO SourceDocument VALUES (
    3, 2,
    'https://www.blackrock.com/ca/investors/en/products/239837/ishares-sptsx-capped-composite-index-etf',
    '2026-09-23T09:25:00.000000Z', NULL,
    'data/raw/blackrock_xic_product_20260801.pdf',
    'BlackRock iShares XIC Product Page');

-- Categories (deterministic ContextKey tokens) ----------------------------
-- Sector categories under the known GICS edition.
INSERT INTO AllocationCategory VALUES (1, 1, 1, 'Information Technology',
                                      'GICS25-45',
                                      'scheme:["S&P Dow Jones Indices","GICS","2025"]');
INSERT INTO AllocationCategory VALUES (2, 1, 1, 'Financials', 'GICS25-40',
                                      'scheme:["S&P Dow Jones Indices","GICS","2025"]');
INSERT INTO AllocationCategory VALUES (3, 1, 1, 'Consumer Discretionary',
                                      'GICS25-25',
                                      'scheme:["S&P Dow Jones Indices","GICS","2025"]');
INSERT INTO AllocationCategory VALUES (4, 1, 1, 'Energy', 'GICS25-10',
                                      'scheme:["S&P Dow Jones Indices","GICS","2025"]');
INSERT INTO AllocationCategory VALUES (5, 1, 1, 'Other Sectors', NULL,
                                      'scheme:["S&P Dow Jones Indices","GICS","2025"]');
-- Geography categories, disclosure-local contexts.
INSERT INTO AllocationCategory VALUES (6, 2, NULL, 'United States', NULL,
    'source:["https://www.vanguard.ca/en/product/etf/equity/9563/vanguard-sp-500-index-etf","2026-09-23T09:15:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (7, 2, NULL, 'Canada', NULL,
    'source:["https://www.vanguard.ca/en/product/etf/equity/9563/vanguard-sp-500-index-etf","2026-09-23T09:15:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (8, 2, NULL, 'Other / Multi-region', NULL,
    'source:["https://www.vanguard.ca/en/product/etf/equity/9563/vanguard-sp-500-index-etf","2026-09-23T09:15:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (9, 2, NULL, 'United States', NULL,
    'source:["https://www.vanguard.ca/en/product/etf/equity/9511/vanguard-us-total-market-index-etf","2026-09-23T09:20:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (10, 2, NULL, 'Other / Multi-region', NULL,
    'source:["https://www.vanguard.ca/en/product/etf/equity/9511/vanguard-us-total-market-index-etf","2026-09-23T09:20:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (11, 2, NULL, 'Canada', NULL,
    'source:["https://www.blackrock.com/ca/investors/en/products/239837/ishares-sptsx-capped-composite-index-etf","2026-09-23T09:25:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (12, 2, NULL, 'United States', NULL,
    'source:["https://www.blackrock.com/ca/investors/en/products/239837/ishares-sptsx-capped-composite-index-etf","2026-09-23T09:25:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (13, 2, NULL, 'Other / Multi-region', NULL,
    'source:["https://www.blackrock.com/ca/investors/en/products/239837/ishares-sptsx-capped-composite-index-etf","2026-09-23T09:25:00.000000Z","geography-table","Geography"]');

-- Snapshots ---------------------------------------------------------------
INSERT INTO AllocationSnapshot VALUES (1, 1, 2, 1, '2026-05-31',
    'Synthetic illustrative weights; identifying facts are real and sourced.',
    'Complete', 'geography-table');
INSERT INTO AllocationSnapshot VALUES (2, 1, 1, 1, '2026-05-31',
    'Synthetic illustrative weights; identifying facts are real and sourced.',
    'Complete', 'sector-table');
INSERT INTO AllocationSnapshot VALUES (3, 2, 2, 2, '2026-05-31',
    'Synthetic illustrative weights; identifying facts are real and sourced.',
    'Complete', 'geography-table');
INSERT INTO AllocationSnapshot VALUES (4, 3, 2, 3, '2026-06-30',
    'Synthetic illustrative weights; identifying facts are real and sourced.',
    'Complete', 'geography-table');
INSERT INTO AllocationSnapshot VALUES (5, 3, 1, 3, '2026-06-30',
    'Synthetic illustrative weights; identifying facts are real and sourced.',
    'Complete', 'sector-table');

-- Entries (17; every Complete snapshot sums to 1.0) -----------------------
-- VFV geography
INSERT INTO AllocationEntry VALUES (1, 1, 6, 0.985);
INSERT INTO AllocationEntry VALUES (2, 1, 7, 0.010);
INSERT INTO AllocationEntry VALUES (3, 1, 8, 0.005);
-- VFV sector (GICS)
INSERT INTO AllocationEntry VALUES (4, 2, 1, 0.310);
INSERT INTO AllocationEntry VALUES (5, 2, 2, 0.130);
INSERT INTO AllocationEntry VALUES (6, 2, 3, 0.105);
INSERT INTO AllocationEntry VALUES (7, 2, 4, 0.040);
INSERT INTO AllocationEntry VALUES (8, 2, 5, 0.415);
-- VUN geography
INSERT INTO AllocationEntry VALUES (9, 3, 9, 0.995);
INSERT INTO AllocationEntry VALUES (10, 3, 10, 0.005);
-- XIC geography
INSERT INTO AllocationEntry VALUES (11, 4, 11, 0.975);
INSERT INTO AllocationEntry VALUES (12, 4, 12, 0.020);
INSERT INTO AllocationEntry VALUES (13, 4, 13, 0.005);
-- XIC sector (GICS)
INSERT INTO AllocationEntry VALUES (14, 5, 2, 0.320);
INSERT INTO AllocationEntry VALUES (15, 5, 4, 0.175);
INSERT INTO AllocationEntry VALUES (16, 5, 1, 0.095);
INSERT INTO AllocationEntry VALUES (17, 5, 5, 0.410);

COMMIT;
