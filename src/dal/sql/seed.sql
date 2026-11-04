-- CSC501 Milestone 4: fully synthetic demonstration seed data.
-- Owner: Mason Li. Run against a database that already has schema.sql applied.
-- The application loads this same dataset through src/dal/seed_data.py inside a
-- validated transaction; this file is the human-readable SQL reference.
--
-- Every record is fictional. Source URLs use the reserved example.invalid
-- domain and are not real addresses; all identities and WeightFraction
-- values are synthetic. This file is a reference and its raw COMMIT can bypass
-- the application-level validator.
PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- Customers ---------------------------------------------------------------
INSERT INTO Customer VALUES (1, '1001', 'Alice', 'Chen',
                             'alice.chen@example.invalid');
INSERT INTO Customer VALUES (2, '1002', 'Brian', 'Li', NULL);

-- Providers (fictional registration details) ------------------------------
INSERT INTO ETFProvider VALUES (1, 'Example Fund Management Ltd.',
                                'SYN-REG-001', 'SYNTHETIC',
                                'https://provider.example.invalid');
INSERT INTO ETFProvider VALUES (2, 'Demonstration Asset Managers Inc.',
                                'SYN-REG-002', 'SYNTHETIC',
                                'https://manager.example.invalid');

-- Dimensions --------------------------------------------------------------
INSERT INTO AllocationDimension VALUES (1, 'Sector');
INSERT INTO AllocationDimension VALUES (2, 'Geography');

-- Classification schemes (one known version, one unknown) -----------------
INSERT INTO ClassificationScheme VALUES (1, 'Example Standards Body',
                                         'Demo Sector Scheme', 'v1', NULL);
INSERT INTO ClassificationScheme VALUES (2, 'Example Fund Management Ltd.',
                                         'Demo Regional Scheme', NULL, NULL);

-- Portfolios --------------------------------------------------------------
INSERT INTO Portfolio VALUES (1, 1, 'P-ALICE-01', 'Growth Portfolio', 'CAD');
INSERT INTO Portfolio VALUES (2, 2, 'P-BRIAN-01', 'Balanced Portfolio', 'CAD');

-- ETFs --------------------------------------------------------------------
INSERT INTO ETF VALUES (1, 1, 'Example Large-Cap Equity ETF',
                        'CA', 'CAD', NULL);
INSERT INTO ETF VALUES (2, 1, 'Example Broad Market Equity ETF',
                        'CA', 'CAD', NULL);
INSERT INTO ETF VALUES (3, 2,
                        'Demonstration Domestic Composite ETF',
                        'CA', 'CAD', NULL);

-- Identifiers (fictional ISIN + Ticker per ETF) ---------------------------
INSERT INTO ETFIdentifier VALUES (1, 1, 'ISIN', 'ZZ0000000001', NULL);
INSERT INTO ETFIdentifier VALUES (2, 1, 'Ticker', 'SYA', 'XDEM');
INSERT INTO ETFIdentifier VALUES (3, 2, 'ISIN', 'ZZ0000000002', NULL);
INSERT INTO ETFIdentifier VALUES (4, 2, 'Ticker', 'SYB', 'XDEM');
INSERT INTO ETFIdentifier VALUES (5, 3, 'ISIN', 'ZZ0000000003', NULL);
INSERT INTO ETFIdentifier VALUES (6, 3, 'Ticker', 'SYC', 'XDEM');

-- Holdings (fictional portfolio weights) ----------------------------------
INSERT INTO Holding VALUES (1, 1, 1, 0.60, '2026-08-01');
INSERT INTO Holding VALUES (2, 1, 3, 0.40, '2026-08-01');
INSERT INTO Holding VALUES (3, 2, 1, 0.30, '2026-08-01');
INSERT INTO Holding VALUES (4, 2, 2, 0.20, '2026-08-01');
INSERT INTO Holding VALUES (5, 2, 3, 0.50, '2026-08-01');

-- Source documents (PublishedAt unknown -> NULL) --------------------------
INSERT INTO SourceDocument VALUES (
    1, 1,
    'https://provider.example.invalid/funds/sya/facts',
    '2026-09-23T09:15:00.000000Z', NULL,
    'data/raw/example_sya_facts_20260716.pdf', 'Example SYA ETF Facts');
INSERT INTO SourceDocument VALUES (
    2, 1,
    'https://provider.example.invalid/funds/syb/facts',
    '2026-09-23T09:20:00.000000Z', NULL,
    'data/raw/example_syb_facts_20260716.pdf', 'Example SYB ETF Facts');
INSERT INTO SourceDocument VALUES (
    3, 2,
    'https://manager.example.invalid/funds/syc/facts',
    '2026-09-23T09:25:00.000000Z', NULL,
    'data/raw/demo_syc_product_20260801.pdf',
    'Demo SYC Product Page');

-- Categories (deterministic ContextKey tokens) ----------------------------
-- Sector categories under the known fictional edition.
INSERT INTO AllocationCategory VALUES (1, 1, 1, 'Information Technology',
                                      'DEMO-45',
                                      'scheme:["Example Standards Body","Demo Sector Scheme","v1"]');
INSERT INTO AllocationCategory VALUES (2, 1, 1, 'Financials', 'DEMO-40',
                                      'scheme:["Example Standards Body","Demo Sector Scheme","v1"]');
INSERT INTO AllocationCategory VALUES (3, 1, 1, 'Consumer Discretionary',
                                      'DEMO-25',
                                      'scheme:["Example Standards Body","Demo Sector Scheme","v1"]');
INSERT INTO AllocationCategory VALUES (4, 1, 1, 'Energy', 'DEMO-10',
                                      'scheme:["Example Standards Body","Demo Sector Scheme","v1"]');
INSERT INTO AllocationCategory VALUES (5, 1, 1, 'Other Sectors', NULL,
                                      'scheme:["Example Standards Body","Demo Sector Scheme","v1"]');
-- Geography categories, disclosure-local contexts.
INSERT INTO AllocationCategory VALUES (6, 2, NULL, 'United States', NULL,
    'source:["https://provider.example.invalid/funds/sya/facts","2026-09-23T09:15:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (7, 2, NULL, 'Canada', NULL,
    'source:["https://provider.example.invalid/funds/sya/facts","2026-09-23T09:15:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (8, 2, NULL, 'Other / Multi-region', NULL,
    'source:["https://provider.example.invalid/funds/sya/facts","2026-09-23T09:15:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (9, 2, NULL, 'United States', NULL,
    'source:["https://provider.example.invalid/funds/syb/facts","2026-09-23T09:20:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (10, 2, NULL, 'Other / Multi-region', NULL,
    'source:["https://provider.example.invalid/funds/syb/facts","2026-09-23T09:20:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (11, 2, NULL, 'Canada', NULL,
    'source:["https://manager.example.invalid/funds/syc/facts","2026-09-23T09:25:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (12, 2, NULL, 'United States', NULL,
    'source:["https://manager.example.invalid/funds/syc/facts","2026-09-23T09:25:00.000000Z","geography-table","Geography"]');
INSERT INTO AllocationCategory VALUES (13, 2, NULL, 'Other / Multi-region', NULL,
    'source:["https://manager.example.invalid/funds/syc/facts","2026-09-23T09:25:00.000000Z","geography-table","Geography"]');

-- Snapshots ---------------------------------------------------------------
INSERT INTO AllocationSnapshot VALUES (1, 1, 2, 1, '2026-05-31',
    'Fully synthetic demonstration: all identities and weights are fictional.',
    'Complete', 'geography-table');
INSERT INTO AllocationSnapshot VALUES (2, 1, 1, 1, '2026-05-31',
    'Fully synthetic demonstration: all identities and weights are fictional.',
    'Complete', 'sector-table');
INSERT INTO AllocationSnapshot VALUES (3, 2, 2, 2, '2026-05-31',
    'Fully synthetic demonstration: all identities and weights are fictional.',
    'Complete', 'geography-table');
INSERT INTO AllocationSnapshot VALUES (4, 3, 2, 3, '2026-06-30',
    'Fully synthetic demonstration: all identities and weights are fictional.',
    'Complete', 'geography-table');
INSERT INTO AllocationSnapshot VALUES (5, 3, 1, 3, '2026-06-30',
    'Fully synthetic demonstration: all identities and weights are fictional.',
    'Complete', 'sector-table');

-- Entries (17; every Complete snapshot sums to 1.0) -----------------------
-- SYA geography
INSERT INTO AllocationEntry VALUES (1, 1, 6, 0.985);
INSERT INTO AllocationEntry VALUES (2, 1, 7, 0.010);
INSERT INTO AllocationEntry VALUES (3, 1, 8, 0.005);
-- SYA sector (fictional scheme)
INSERT INTO AllocationEntry VALUES (4, 2, 1, 0.310);
INSERT INTO AllocationEntry VALUES (5, 2, 2, 0.130);
INSERT INTO AllocationEntry VALUES (6, 2, 3, 0.105);
INSERT INTO AllocationEntry VALUES (7, 2, 4, 0.040);
INSERT INTO AllocationEntry VALUES (8, 2, 5, 0.415);
-- SYB geography
INSERT INTO AllocationEntry VALUES (9, 3, 9, 0.995);
INSERT INTO AllocationEntry VALUES (10, 3, 10, 0.005);
-- SYC geography
INSERT INTO AllocationEntry VALUES (11, 4, 11, 0.975);
INSERT INTO AllocationEntry VALUES (12, 4, 12, 0.020);
INSERT INTO AllocationEntry VALUES (13, 4, 13, 0.005);
-- SYC sector (fictional scheme)
INSERT INTO AllocationEntry VALUES (14, 5, 2, 0.320);
INSERT INTO AllocationEntry VALUES (15, 5, 4, 0.175);
INSERT INTO AllocationEntry VALUES (16, 5, 1, 0.095);
INSERT INTO AllocationEntry VALUES (17, 5, 5, 0.410);

COMMIT;
