-- Fixture for eval-sql-014. Portable SQL: runs on SQLite (the scorer in this lab) and on Postgres.
-- Edge cases on purpose: a customer whose first order was in 2025 but who also ordered in 2026 (101),
-- a first order a few minutes after New Year (102), one late on 31 December (105), and one at
-- exactly 2027-01-01 00:00 (106). The correct answer is 3 customers: 102, 103 and 105.
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    total_usd   NUMERIC(10, 2) NOT NULL,
    created_at  TIMESTAMP NOT NULL
);
INSERT INTO orders VALUES (1, 101, 40.00, '2025-11-03 09:15:00');
INSERT INTO orders VALUES (2, 101, 25.50, '2026-02-10 14:00:00');
INSERT INTO orders VALUES (3, 102, 60.00, '2026-01-01 00:05:00');
INSERT INTO orders VALUES (4, 102, 12.00, '2026-03-22 18:40:00');
INSERT INTO orders VALUES (5, 103, 99.90, '2026-07-19 11:30:00');
INSERT INTO orders VALUES (6, 104, 15.00, '2025-06-30 08:00:00');
INSERT INTO orders VALUES (7, 105, 75.25, '2026-12-31 23:30:00');
INSERT INTO orders VALUES (8, 106, 20.00, '2027-01-01 00:00:00');
