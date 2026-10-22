-- Two yearly series, one row per year. Constraints keep bad data out of the database
-- even if it arrives through some path other than the cleaning code.

CREATE TABLE establishments (
    year       INTEGER PRIMARY KEY CHECK (year BETWEEN 1900 AND 2100),
    businesses INTEGER NOT NULL CHECK (businesses > 0)
);

CREATE TABLE arrivals (
    year     INTEGER PRIMARY KEY CHECK (year BETWEEN 1900 AND 2100),
    tourists INTEGER NOT NULL CHECK (tourists > 0)
);

-- Joined view used by most analysis queries.
CREATE VIEW tourism_yearly AS
SELECT a.year,
       e.businesses,
       a.tourists,
       ROUND(1.0 * a.tourists / e.businesses, 1) AS tourists_per_business
FROM arrivals a
JOIN establishments e ON e.year = a.year;
