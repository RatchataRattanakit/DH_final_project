# Digital History Project: How Xi Jinping Embeds Nationalism into Chinese Citizens Through State Media

## Project Overview

A computational digital history project that uses GDELT BigQuery API to analyze how Chinese state media systematically shifted the language and framing of patriotism under Xi Jinping — comparing the pre-Xi era (2008–2012) against the Xi era (2012–2024).

**Core Argument:**
> Xi Jinping did not merely inherit Chinese nationalism — he rewired it. Through state media, the Party fused patriotic identity with consumer behavior, geopolitical grievance, and everyday life. This project measures that fusion computationally.

---

## Research Question

*How did Chinese state media change the frequency, context, and framing of nationalist language between the pre-Xi era (2008–2012) and the Xi era (2012–2024)?*

---

## Methodology

Three computational methods applied in sequence:

### 1. Keyword Frequency over Time
Track how often key nationalist terms appear in state media, measured annually from 2008–2024.

**Keywords to track (two groups):**

| Group | Chinese | Pinyin | English |
|-------|---------|--------|---------|
| Nationalism | 爱国 | ài guó | patriotism / love the country |
| Nationalism | 民族主义 | mínzú zhǔyì | nationalism |
| Xi Rhetoric | 中国梦 | zhōngguó mèng | China Dream |
| Xi Rhetoric | 民族复兴 | mínzú fùxīng | national rejuvenation |
| Consumer | 国货 | guó huò | domestic goods |
| Consumer | 抵制 | dǐ zhì | boycott |
| Consumer | 国潮 | guó cháo | Guochao / national wave |

### 2. Framing Analysis (Tone Scoring)
Use GDELT's automatic tone scoring to measure how aggressively each keyword is framed — negative tone = threat framing, positive tone = pride framing.

### 3. Event-Correlation Analysis
Correlate spikes in nationalist language with key political events:
- 2008: Beijing Olympics
- 2012: Xi takes power / Diaoyu Islands dispute
- 2017: THAAD crisis (South Korea)
- 2019: NBA/Hong Kong controversy
- 2021: Xinjiang cotton / H&M boycott
- 2022: Beijing Winter Olympics / Ukraine war

---

## Data Sources

### Primary: GDELT BigQuery (already set up)
- **Dataset:** `gdelt-bq.gdeltv2.gkg_partitioned`
- **Access:** Google BigQuery (free tier — 1TB/month)
- **Coverage:** 2015–present (full GDELT v2)
- **What it provides:** Tone scores, article volume, themes, organization mentions
- **Authentication:** Google Cloud service account JSON key

### Secondary: GDELT v1 (for 2008–2014 coverage)
- **Dataset:** `gdelt-bq.full_data.events` 
- **Coverage:** 1979–present
- **Note:** Different schema from v2, requires separate query

### Tertiary: People's Daily keyword proxy via GDELT
- Filter by `SourceCommonName LIKE '%peopledaily%'` OR `SourceCommonName LIKE '%xinhua%'`

---

## BigQuery SQL Queries

### Query 1: Keyword Frequency by Year (Xi vs pre-Xi)

```sql
SELECT
  EXTRACT(YEAR FROM PARSE_DATE('%Y%m%d', CAST(SUBSTR(CAST(DATE AS STRING), 1, 8) AS STRING))) as year,
  
  -- Count articles mentioning each nationalist keyword
  COUNTIF(UPPER(V2Themes) LIKE '%PATRIOTISM%' 
    OR LOWER(DocumentIdentifier) LIKE '%aiguo%'
    OR LOWER(DocumentIdentifier) LIKE '%爱国%') as patriotism_count,
    
  COUNTIF(UPPER(V2Organizations) LIKE '%CHINA DREAM%'
    OR LOWER(DocumentIdentifier) LIKE '%zhongguomeng%') as china_dream_count,
    
  COUNTIF(UPPER(V2Themes) LIKE '%NATIONALISM%') as nationalism_theme_count,
  
  COUNTIF(UPPER(V2Organizations) LIKE '%LI-NING%'
    OR UPPER(V2Organizations) LIKE '%GUOCHAO%'
    OR LOWER(DocumentIdentifier) LIKE '%guochao%') as guochao_count,
    
  -- Average tone for nationalist-coded articles  
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
```

### Query 2: Consumer Nationalism Keywords over Time

```sql
SELECT
  PARSE_DATE('%Y%m%d', CAST(SUBSTR(CAST(DATE AS STRING), 1, 8) AS STRING)) as pub_date,
  
  -- Foreign brand boycott articles
  COUNTIF(
    UPPER(V2Organizations) LIKE '%H&M%'
    OR UPPER(V2Organizations) LIKE '%NIKE%'
    OR UPPER(V2Organizations) LIKE '%LOTTE%'
    OR UPPER(V2Organizations) LIKE '%NBA%'
  ) as foreign_brand_mentions,
  
  -- Domestic brand pride articles  
  COUNTIF(
    UPPER(V2Organizations) LIKE '%LI-NING%'
    OR UPPER(V2Organizations) LIKE '%HUAWEI%'
    OR UPPER(V2Organizations) LIKE '%ANTA%'
    OR UPPER(V2Organizations) LIKE '%BYD%'
  ) as domestic_brand_mentions,
  
  -- Tone: negative = hostile framing of foreign brands
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
```

### Query 3: Xi Rhetoric Keywords — Monthly Trend

```sql
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
```

---

## Python Data Pipeline

### Setup

```bash
pip install google-cloud-bigquery pandas matplotlib db-dtypes pyarrow
```

Place `bigquery_key.json` (Google Cloud service account key) in project root.

### Authentication

```python
from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bigquery_key.json"
client = bigquery.Client()
```

### Expected Output Files

After running the pipeline, the following CSVs should be generated:

| File | Contents |
|------|----------|
| `keyword_frequency_annual.csv` | Yearly counts of each keyword group |
| `consumer_nationalism_daily.csv` | Daily foreign vs domestic brand mentions + tone |
| `xi_rhetoric_monthly.csv` | Monthly China Dream / rejuvenation keyword counts |
| `event_correlation.csv` | Keyword spikes aligned with political events |

---

## Visualization Requirements

Build an **interactive HTML dashboard** with the following views:

### View 1: Keyword Frequency Timeline (Main Chart)
- X-axis: Year (2015–2024)
- Y-axis: Article count (normalized per 100k articles)
- Lines: One per keyword group (nationalism / Xi rhetoric / consumer)
- **Vertical annotations** marking key political events
- Toggle between raw count and normalized count
- Color scheme: Dark/editorial aesthetic

### View 2: Pre-Xi vs Xi Era Comparison (Bar Chart)
- Side-by-side bars: 2015–2018 average vs 2019–2024 average
- One bar per keyword
- Show percentage increase

### View 3: Foreign vs Domestic Brand Tone (Line Chart)
- Two lines: foreign brand tone vs domestic brand tone
- Show divergence growing over time
- Annotate boycott events

### View 4: Event Correlation Heatmap
- X-axis: Month/Year
- Y-axis: Keyword
- Color: Intensity of usage (darker = more mentions)
- Shows which events triggered which keywords

---

## Project Structure

```
DH-project/
├── bigquery_key.json          # Google Cloud credentials (DO NOT COMMIT)
├── collect_data.py            # Pulls all data from BigQuery
├── process_data.py            # Cleans and normalizes CSVs
├── visualize.py               # Generates static charts (matplotlib)
├── dashboard/
│   └── index.html             # Interactive dashboard (vanilla JS + D3)
├── data/
│   ├── keyword_frequency_annual.csv
│   ├── consumer_nationalism_daily.csv
│   ├── xi_rhetoric_monthly.csv
│   └── event_correlation.csv
└── README.md
```

---

## Key Political Events to Annotate

```python
EVENTS = [
    {"date": "2012-11-15", "label": "Xi takes power",         "type": "political"},
    {"date": "2013-03-17", "label": "China Dream speech",     "type": "rhetoric"},
    {"date": "2015-05-01", "label": "Made in China 2025",     "type": "policy"},
    {"date": "2017-03-07", "label": "THAAD / Lotte boycott",  "type": "boycott"},
    {"date": "2019-10-07", "label": "NBA controversy",        "type": "boycott"},
    {"date": "2021-03-24", "label": "H&M / Xinjiang cotton",  "type": "boycott"},
    {"date": "2022-02-04", "label": "Beijing Winter Olympics","type": "political"},
    {"date": "2022-11-01", "label": "Guochao peaks",          "type": "consumer"},
]
```

---

## Findings to Prove

The analysis should demonstrate:

1. **Frequency surge** — Nationalist keywords increased significantly post-2012 in state media
2. **Consumer fusion** — 国货 / Guochao language grew in parallel with boycott events, not independently
3. **Rhetorical escalation** — China Dream / rejuvenation language spiked around geopolitical flashpoints
4. **Framing shift** — Tone of foreign brand coverage became more hostile over time while domestic brand coverage became more positive
5. **Coordination signature** — Multiple keywords spike simultaneously during engineered events (not organically)

---

## Central Thesis

> *Under Xi Jinping, Chinese state media did not simply report on nationalism — it manufactured the conditions for it. By systematically linking patriotic language to consumer choices, economic grievances, and geopolitical identity, the Party transformed nationalism from a political sentiment into a daily behavioral norm. This project measures that transformation computationally.*

---

## Notes for Claude Code

- All data fetching goes through `collect_data.py` — no hardcoded data
- CSVs in `data/` are the source of truth for the dashboard
- Dashboard must work as a single `index.html` file (no server required)
- Use D3.js for all charts (load from CDN)
- Dashboard should be readable as a standalone digital history essay, not just charts
- Include methodology notes inline with each visualization
- BigQuery credentials are in `bigquery_key.json` — use `google-cloud-bigquery` Python library
