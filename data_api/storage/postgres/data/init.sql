CREATE TABLE IF NOT EXISTS project_info (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(128) NOT NULL,
    project_name VARCHAR(128) NOT NULL,
    description TEXT,
    contract_address VARCHAR(128) NOT NULL,
    slug VARCHAR(128) UNIQUE NOT NULL,
    twitter_account_username VARCHAR(24),
    icon_url TEXT,
    website_url TEXT,
    blockchain_id INT NOT NULL,
    curated BOOLEAN
);

CREATE INDEX IF NOT EXISTS contract_address_idx ON project_info (contract_address);
CREATE INDEX IF NOT EXISTS slug_idx ON project_info (slug);
CREATE INDEX IF NOT EXISTS twitter_account_username_idx ON project_info (twitter_account_username);
CREATE INDEX IF NOT EXISTS blockchain_id_idx ON project_info (blockchain_id);
CREATE INDEX IF NOT EXISTS curated_idx ON project_info (curated);
CREATE INDEX IF NOT EXISTS blockchain_id_slug_idx ON project_info (blockchain_id, slug);

CREATE TABLE IF NOT EXISTS twitter_trends (
    id SERIAL PRIMARY KEY,
    twitter_account_username VARCHAR(24) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    mentions_number INT NOT NULL, 
    followers_number INT NOT NULL, 
    start_time TIMESTAMP
);

CREATE INDEX IF NOT EXISTS timestamp_idx ON twitter_trends (timestamp);

CREATE TABLE IF NOT EXISTS project_stats (
    id SERIAL PRIMARY KEY,
    contract_address VARCHAR(128),
    project_id VARCHAR(128),
    timestamp TIMESTAMP NOT NULL,
    floor_price FLOAT(8),
    total_supply INT,
    total_sales INT,
    total_volume INT,
    market_cap INT,
    holders VARCHAR(128) ARRAY, 
    description TEXT
);

CREATE INDEX IF NOT EXISTS project_id_idx ON project_stats (project_id);
CREATE INDEX IF NOT EXISTS timestamp_idx ON project_stats (timestamp);
CREATE INDEX IF NOT EXISTS floor_price_idx ON project_stats (floor_price);

CREATE TYPE nft_creator AS (
    address VARCHAR(64),
    verified BOOLEAN,
    share INT
);

CREATE TYPE media_file AS (
    uri VARCHAR(128),
    file_type VARCHAR(24)
);

CREATE TYPE attribute AS (
    name VARCHAR(32),
    value VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS nft_data (
    id SERIAL PRIMARY KEY,
    blockchain_id INT,
    blockchain_name VARCHAR(128),
    project_id VARCHAR(128),
    project_name VARCHAR(128),
    project_slug VARCHAR(128),
    market_id INT, 
    token_key VARCHAR(128),
    owner VARCHAR(128),
    token_id VARCHAR(128),
    token_name VARCHAR(128),
    token_slug VARCHAR(128),
    description TEXT,
    symbol VARCHAR(24),
    primary_sale_happened BOOLEAN,
    last_market_activity VARCHAR(24),
    timestamp_of_market_activity TIMESTAMP,
    event_timestamp TIMESTAMP,
    metadata_uri VARCHAR(64),
    transaction_hash VARCHAR(128),
    price FLOAT(8),
    price_currency VARCHAR(24),
    creators nft_creator ARRAY,
    edition VARCHAR(64),
    external_url VARCHAR(64),
    media_files media_file ARRAY,
    attributes attribute ARRAY
);

CREATE INDEX IF NOT EXISTS project_id_idx ON nft_data (project_id);
CREATE INDEX IF NOT EXISTS last_market_activity_idx ON nft_data (last_market_activity);
CREAtE INDEX IF NOT EXISTS timestamp_of_market_activity_idx ON nft_data (timestamp_of_market_activity);