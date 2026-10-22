-- Each query starts with "-- name: <query_name>" and is loaded by tourism/analysis.py.

-- name: yearly_growth
-- Year-on-year growth of both series, using the LAG window function.
SELECT year,
       businesses,
       tourists,
       tourists_per_business,
       ROUND(100.0 * (tourists - LAG(tourists) OVER (ORDER BY year))
             / LAG(tourists) OVER (ORDER BY year), 1)     AS tourists_yoy_pct,
       ROUND(100.0 * (businesses - LAG(businesses) OVER (ORDER BY year))
             / LAG(businesses) OVER (ORDER BY year), 1)   AS businesses_yoy_pct
FROM tourism_yearly
ORDER BY year;

-- name: biggest_arrival_changes
-- The five largest year-on-year moves in arrivals, up or down.
WITH changes AS (
    SELECT year,
           tourists,
           LAG(tourists) OVER (ORDER BY year) AS previous
    FROM arrivals
)
SELECT year,
       previous AS previous_year_tourists,
       tourists,
       ROUND(100.0 * (tourists - previous) / previous, 1) AS change_pct
FROM changes
WHERE previous IS NOT NULL
ORDER BY ABS(1.0 * (tourists - previous) / previous) DESC
LIMIT 5;

-- name: years_with_declines
-- Years in which arrivals or businesses fell compared with the year before.
WITH changes AS (
    SELECT year,
           tourists,
           businesses,
           LAG(tourists)   OVER (ORDER BY year) AS prev_tourists,
           LAG(businesses) OVER (ORDER BY year) AS prev_businesses
    FROM tourism_yearly
)
SELECT year,
       CASE WHEN tourists   < prev_tourists   THEN 1 ELSE 0 END AS tourists_fell,
       CASE WHEN businesses < prev_businesses THEN 1 ELSE 0 END AS businesses_fell
FROM changes
WHERE tourists < prev_tourists OR businesses < prev_businesses
ORDER BY year;

-- name: five_year_periods
-- Averages per consecutive five-year block, counted from the first year in the data.
SELECT MIN(year) || '-' || MAX(year)       AS period,
       ROUND(AVG(tourists))                AS avg_tourists,
       ROUND(AVG(businesses))              AS avg_businesses,
       ROUND(AVG(tourists_per_business), 1) AS avg_tourists_per_business
FROM tourism_yearly
GROUP BY (year - (SELECT MIN(year) FROM tourism_yearly)) / 5
ORDER BY MIN(year);

-- name: peak_tourists_per_business
-- Years ranked by how many tourists arrived per accommodation business.
SELECT year, tourists_per_business
FROM tourism_yearly
ORDER BY tourists_per_business DESC
LIMIT 3;
