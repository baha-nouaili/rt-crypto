CREATE DATABASE rt_crypto;

\c rt_crypto;

CREATE TABLE market_informations (
  instrument_name VARCHAR(255),
  currency VARCHAR(255),
  maturity VARCHAR(255),
  strike DECIMAL,
  type CHAR(1),
  created_at TIMESTAMP,
  underlying_price DECIMAL,
  timestamp TIMESTAMP,
  settlement_price DECIMAL,
  open_interest DECIMAL,
  min_price DECIMAL,
  max_price DECIMAL,
  mark_price DECIMAL,
  mark_iv DECIMAL,
  last_price DECIMAL,
  interest_rate DECIMAL,
  index_price DECIMAL,
  bid_iv DECIMAL,
  best_bid_price DECIMAL,
  best_bid_amount DECIMAL,
  best_ask_price DECIMAL,
  best_ask_amount DECIMAL,
  ask_iv DECIMAL
)
