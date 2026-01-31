CREATE TABLE IF NOT EXISTS campaign_daily (
  date TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  campaign_id TEXT NOT NULL,
  campaign_name TEXT NOT NULL,
  impressions INTEGER NOT NULL,
  clicks INTEGER NOT NULL,
  cost_micros INTEGER NOT NULL,
  conversions REAL NOT NULL,
  conversions_value REAL NOT NULL,
  PRIMARY KEY (date, customer_id, campaign_id)
);

CREATE TABLE IF NOT EXISTS search_term_daily (
  date TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  campaign_id TEXT NOT NULL,
  ad_group_id TEXT NOT NULL,
  search_term TEXT NOT NULL,
  impressions INTEGER NOT NULL,
  clicks INTEGER NOT NULL,
  cost_micros INTEGER NOT NULL,
  conversions REAL NOT NULL,
  conversions_value REAL NOT NULL,
  PRIMARY KEY (date, customer_id, campaign_id, ad_group_id, search_term)
);
