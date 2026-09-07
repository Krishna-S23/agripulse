-- =====================================================================
-- AgriPulse — BigQuery Schema
-- Dataset: agripulse_data
-- Run this once against your GCP project to create the dataset + tables.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS `agripulse_data`
OPTIONS (location = 'asia-south1');

-- ---------------------------------------------------------------------
-- farm: one row per registered farm profile (app-written, via Firestore
-- mirror or direct backend insert)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agripulse_data.farm` (
  farm_id       STRING NOT NULL,
  district      STRING NOT NULL,
  location      STRING,            -- taluk/village
  crop          STRING NOT NULL,   -- 'Tomato' | 'Onion' (extendable)
  area_acres    FLOAT64,
  growth_stage  STRING,
  soil_type     STRING,
  owner_name    STRING,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY farm_id;

-- ---------------------------------------------------------------------
-- weather: daily weather by district (ingested from NASA POWER /
-- Open-Meteo)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agripulse_data.weather` (
  date          DATE NOT NULL,
  district      STRING NOT NULL,
  temperature_c FLOAT64,
  rainfall_mm   FLOAT64,
  humidity_pct  FLOAT64,
  rain_prob_pct FLOAT64,           -- from forecast source only; NULL for historical rows
  source        STRING             -- 'nasa_power' | 'open_meteo'
)
PARTITION BY date
CLUSTER BY district;

-- ---------------------------------------------------------------------
-- soil_conditions: per-farm soil readings (synthetic for MVP)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agripulse_data.soil_conditions` (
  farm_id   STRING NOT NULL,
  date      DATE NOT NULL,
  moisture  FLOAT64,   -- percent
  ph        FLOAT64,
  nitrogen  STRING     -- 'Low' | 'Adequate' | 'High'
)
PARTITION BY date
CLUSTER BY farm_id;

-- ---------------------------------------------------------------------
-- market_prices: daily mandi prices (ingested from Agmarknet)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agripulse_data.market_prices` (
  date         DATE NOT NULL,
  crop         STRING NOT NULL,
  market       STRING NOT NULL,
  district     STRING,
  modal_price  FLOAT64,   -- INR per quintal
  min_price    FLOAT64,
  max_price    FLOAT64,
  arrivals     FLOAT64    -- tonnes
)
PARTITION BY date
CLUSTER BY crop, market;

-- ---------------------------------------------------------------------
-- crop_history: annual district-level production/yield (data.gov.in)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agripulse_data.crop_history` (
  year        INT64 NOT NULL,
  district    STRING NOT NULL,
  crop        STRING NOT NULL,
  production  FLOAT64,   -- tonnes
  yield       FLOAT64    -- tonnes/hectare
)
CLUSTER BY district, crop;

-- =====================================================================
-- Views — pre-aggregated, what the agents actually query
-- =====================================================================

-- 7-day rainfall + temp trend per district
CREATE OR REPLACE VIEW `agripulse_data.v_rainfall_7day` AS
SELECT
  district,
  date,
  rainfall_mm,
  temperature_c,
  humidity_pct,
  rain_prob_pct,
  AVG(rainfall_mm) OVER (
    PARTITION BY district ORDER BY UNIX_DATE(date)
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS rainfall_7day_avg
FROM `agripulse_data.weather`;

-- Latest soil reading per farm
CREATE OR REPLACE VIEW `agripulse_data.v_latest_soil` AS
SELECT farm_id, date, moisture, ph, nitrogen
FROM `agripulse_data.soil_conditions`
QUALIFY ROW_NUMBER() OVER (PARTITION BY farm_id ORDER BY date DESC) = 1;

-- Weekly price trend per crop/market vs. prior 7 days
CREATE OR REPLACE VIEW `agripulse_data.v_weekly_price_trend` AS
SELECT
  crop,
  market,
  district,
  date,
  modal_price,
  arrivals,
  AVG(modal_price) OVER (
    PARTITION BY crop, market ORDER BY UNIX_DATE(date)
    ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
  ) AS prior_7day_avg_price,
  SAFE_DIVIDE(
    modal_price - AVG(modal_price) OVER (
      PARTITION BY crop, market ORDER BY UNIX_DATE(date)
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ),
    AVG(modal_price) OVER (
      PARTITION BY crop, market ORDER BY UNIX_DATE(date)
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    )
  ) * 100 AS pct_change_vs_prior_week
FROM `agripulse_data.market_prices`;

-- District/crop historical yield trend (year over year)
CREATE OR REPLACE VIEW `agripulse_data.v_yield_trend` AS
SELECT
  district,
  crop,
  year,
  yield,
  yield - LAG(yield) OVER (PARTITION BY district, crop ORDER BY year) AS yield_change_yoy
FROM `agripulse_data.crop_history`;
