-- Second fixture for eval-sql-014: the same data without order 2, so customer 101 has no 2026 order.
-- It exists to break coincidences: a wrong query can return the right number on one fixture when two
-- of its mistakes cancel out (see scorers.py). The correct answer is still 3: customers 102, 103, 105.
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    total_usd   NUMERIC(10, 2) NOT NULL,
    created_at  TIMESTAMP NOT NULL
);
INSERT INTO orders VALUES (1, 101, 40.00, '2025-11-03 09:15:00');
INSERT INTO orders VALUES (3, 102, 60.00, '2026-01-01 00:05:00');
INSERT INTO orders VALUES (4, 102, 12.00, '2026-03-22 18:40:00');
INSERT INTO orders VALUES (5, 103, 99.90, '2026-07-19 11:30:00');
INSERT INTO orders VALUES (6, 104, 15.00, '2025-06-30 08:00:00');
INSERT INTO orders VALUES (7, 105, 75.25, '2026-12-31 23:30:00');
INSERT INTO orders VALUES (8, 106, 20.00, '2027-01-01 00:00:00');
