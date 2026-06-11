#!/usr/bin/env python3
"""
collect_data.py
Pulls nationalist keyword frequency data from GDELT BigQuery.

Requires:
  - bigquery_key.json in project root (Google Cloud service account key)
  - pip install google-cloud-bigquery pandas db-dtypes pyarrow
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery

KEY_FILE = "bigquery_key.json"

if not os.path.exists(KEY_FILE):
    print(f"ERROR: {KEY_FILE} not found.")
    print("Place your Google Cloud service account key in the project root.")
    print("See: https://cloud.google.com/bigquery/docs/authentication/service-account-file")
    sys.exit(1)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_FILE

try:
    client = bigquery.Client()
    print("BigQuery connection established.")
except Exception as e:
    print(f"ERROR: Failed to connect to BigQuery: {e}")
    sys.exit(1)

os.makedirs("data", exist_ok=True)

# ---------------------------------------------------------------------------
# Query 1: Keyword Frequency by Year (2015–2024)
# ---------------------------------------------------------------------------
print("\n[1/3] Keyword Frequency by Year...")

QUERY_1 = """
SELECT
  EXTRACT(YEAR FROM PARSE_DATE('%Y%m%d', CAST(SUBSTR(CAST(DATE AS STRING), 1, 8) AS STRING))) as year,

  COUNTIF(UPPER(V2Themes) LIKE '%PATRIOTISM%'
    OR LOWER(DocumentIdentifier) LIKE '%aiguo%'
    OR LOWER(DocumentIdentifier) LIKE '%爱国%') as patriotism_count,

  COUNTIF(UPPER(V2Organizations) LIKE '%CHINA DREAM%'
    OR LOWER(DocumentIdentifier) LIKE '%zhongguomeng%') as china_dream_count,

  COUNTIF(UPPER(V2Themes) LIKE '%NATIONALISM%') as nationalism_theme_count,

  COUNTIF(UPPER(V2Organizations) LIKE '%LI-NING%'
    OR UPPER(V2Organizations) LIKE '%GUOCHAO%'
    OR LOWER(DocumentIdentifier) LIKE '%guochao%') as guochao_count,

  AVG(CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64)) as avg_tone,

  COUNT(*) as total_china_articles

FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP('2015-01-01') AND TIMESTAMP('2024-12-31')
  AND (
    SourceCommonName LIKE '%.cn%'
    OR SourceCommonName LIKE '%xinhua%'
    OR SourceCommonName LIKE '%chinadaily%'
    OR SourceCommonName LIKE '%globaltimes%'
    OR SourceCommonName LIKE '%peopledaily%'
    OR SourceCommonName LIKE '%cgtn%'
  )
GROUP BY year
ORDER BY year
"""

try:
    df1 = client.query(QUERY_1).to_dataframe()
    df1.to_csv("data/keyword_frequency_annual.csv", index=False)
    print(f"  Saved: data/keyword_frequency_annual.csv ({len(df1)} rows)")
except Exception as e:
    print(f"  ERROR running Query 1: {e}")

# ---------------------------------------------------------------------------
# Query 2: Consumer Nationalism — Foreign vs Domestic Brand Coverage (daily)
# ---------------------------------------------------------------------------
print("\n[2/3] Consumer Nationalism (daily)...")

QUERY_2 = """
SELECT
  PARSE_DATE('%Y%m%d', CAST(SUBSTR(CAST(DATE AS STRING), 1, 8) AS STRING)) as pub_date,

  COUNTIF(
    UPPER(V2Organizations) LIKE '%H&M%'
    OR UPPER(V2Organizations) LIKE '%NIKE%'
    OR UPPER(V2Organizations) LIKE '%LOTTE%'
    OR UPPER(V2Organizations) LIKE '%NBA%'
  ) as foreign_brand_mentions,

  COUNTIF(
    UPPER(V2Organizations) LIKE '%LI-NING%'
    OR UPPER(V2Organizations) LIKE '%HUAWEI%'
    OR UPPER(V2Organizations) LIKE '%ANTA%'
    OR UPPER(V2Organizations) LIKE '%BYD%'
  ) as domestic_brand_mentions,

  AVG(CASE WHEN UPPER(V2Organizations) LIKE '%H&M%'
           OR UPPER(V2Organizations) LIKE '%NIKE%'
       THEN CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) END) as foreign_brand_tone,

  AVG(CASE WHEN UPPER(V2Organizations) LIKE '%LI-NING%'
           OR UPPER(V2Organizations) LIKE '%HUAWEI%'
       THEN CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) END) as domestic_brand_tone

FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP('2015-01-01') AND TIMESTAMP('2024-12-31')
  AND (
    SourceCommonName LIKE '%.cn%'
    OR SourceCommonName LIKE '%xinhua%'
    OR SourceCommonName LIKE '%globaltimes%'
  )
GROUP BY pub_date
ORDER BY pub_date
"""

try:
    df2 = client.query(QUERY_2).to_dataframe()
    df2.to_csv("data/consumer_nationalism_daily.csv", index=False)
    print(f"  Saved: data/consumer_nationalism_daily.csv ({len(df2)} rows)")
except Exception as e:
    print(f"  ERROR running Query 2: {e}")

# ---------------------------------------------------------------------------
# Query 3: Xi Rhetoric Keywords — Monthly Trend
# ---------------------------------------------------------------------------
print("\n[3/3] Xi Rhetoric Keywords (monthly)...")

QUERY_3 = """
SELECT
  FORMAT_DATE('%Y-%m', PARSE_DATE('%Y%m%d', CAST(SUBSTR(CAST(DATE AS STRING), 1, 8) AS STRING))) as year_month,

  COUNTIF(V2Themes LIKE '%CHINESE_DREAM%'
    OR DocumentIdentifier LIKE '%china-dream%'
    OR DocumentIdentifier LIKE '%zhongguomeng%') as china_dream,

  COUNTIF(V2Themes LIKE '%NATIONAL_REJUVENATION%'
    OR DocumentIdentifier LIKE '%rejuvenation%'
    OR DocumentIdentifier LIKE '%fuxing%') as national_rejuvenation,

  COUNTIF(V2Themes LIKE '%MADE_IN_CHINA%'
    OR DocumentIdentifier LIKE '%made-in-china-2025%') as made_in_china_2025,

  COUNT(*) as total_articles,
  AVG(CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64)) as avg_tone

FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP('2015-01-01') AND TIMESTAMP('2024-12-31')
  AND (
    SourceCommonName LIKE '%.cn%'
    OR SourceCommonName LIKE '%xinhua%'
    OR SourceCommonName LIKE '%chinadaily%'
    OR SourceCommonName LIKE '%globaltimes%'
  )
GROUP BY year_month
ORDER BY year_month
"""

try:
    df3 = client.query(QUERY_3).to_dataframe()
    df3.to_csv("data/xi_rhetoric_monthly.csv", index=False)
    print(f"  Saved: data/xi_rhetoric_monthly.csv ({len(df3)} rows)")
except Exception as e:
    print(f"  ERROR running Query 3: {e}")

print("\nData collection complete.")
print("Next: python process_data.py")
