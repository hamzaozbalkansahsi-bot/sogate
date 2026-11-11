-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/001_commerce.sql | Açıklama: Ticaret ve depo şeması.
CREATE TABLE categories (slug text PRIMARY KEY, name text NOT NULL, name_en text NOT NULL);
CREATE TABLE products (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text, slug text NOT NULL UNIQUE,
 name text NOT NULL, name_en text NOT NULL, description text NOT NULL DEFAULT '', description_en text NOT NULL DEFAULT '',
 category text NOT NULL REFERENCES categories(slug), brand text NOT NULL DEFAULT '', image text NOT NULL,
 material text NOT NULL DEFAULT '', status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','review','published','closed','archived')),
 warnings text NOT NULL DEFAULT '', care text NOT NULL DEFAULT '', manufacturer text, origin text,
 fixture boolean NOT NULL DEFAULT false, attributes jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE variants (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text, product_id text NOT NULL REFERENCES products(id), sku text NOT NULL UNIQUE,
 name text NOT NULL, barcode text UNIQUE, price_minor bigint NOT NULL CHECK(price_minor>=0 AND price_minor<=9000000000000),
 cost_minor bigint NOT NULL DEFAULT 0 CHECK(cost_minor>=0 AND cost_minor<=9000000000000), currency text NOT NULL DEFAULT 'TRY' CHECK(currency IN ('TRY','EUR','USD','GBP')),
 color text, size text, weight_grams integer NOT NULL DEFAULT 0 CHECK(weight_grams>=0), package_dimensions jsonb,
 battery_type text, battery_capacity_mah integer, ingredients text, hygiene_sealed boolean NOT NULL DEFAULT false,
 active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX products_category_status ON products(category,status);
CREATE INDEX products_search ON products USING gin(to_tsvector('simple', name || ' ' || name_en || ' ' || description));
CREATE TABLE product_documents (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,variant_id text NOT NULL REFERENCES variants(id),country text NOT NULL,kind text NOT NULL,reference text NOT NULL,valid_from date NOT NULL,valid_until date,reviewed boolean NOT NULL DEFAULT false);
CREATE TABLE product_eligibility (variant_id text NOT NULL REFERENCES variants(id),country text NOT NULL,approved boolean NOT NULL DEFAULT false,required_document_kind text,review_note text NOT NULL DEFAULT '',PRIMARY KEY(variant_id,country));
CREATE TABLE variant_prices (variant_id text NOT NULL REFERENCES variants(id),currency text NOT NULL CHECK(currency IN ('TRY','EUR','USD','GBP')),amount_minor bigint NOT NULL CHECK(amount_minor>=0 AND amount_minor<=9000000000000),valid_from timestamptz NOT NULL DEFAULT now(),valid_until timestamptz,PRIMARY KEY(variant_id,currency));
CREATE TABLE exchange_rates (base_currency text NOT NULL,quote_currency text NOT NULL,rate numeric(20,10) NOT NULL CHECK(rate>0),source text NOT NULL,observed_at timestamptz NOT NULL,expires_at timestamptz NOT NULL,buffer_bps integer NOT NULL DEFAULT 0,PRIMARY KEY(base_currency,quote_currency));
CREATE TABLE warehouses (id text PRIMARY KEY, name text NOT NULL);
CREATE TABLE warehouse_locations (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,warehouse_id text NOT NULL REFERENCES warehouses(id),code text NOT NULL,UNIQUE(warehouse_id,code));
CREATE TABLE inventory_balance (
 variant_id text NOT NULL REFERENCES variants(id),warehouse_id text NOT NULL REFERENCES warehouses(id),
 on_hand integer NOT NULL DEFAULT 0 CHECK(on_hand>=0),quarantine integer NOT NULL DEFAULT 0 CHECK(quarantine>=0),safety_stock integer NOT NULL DEFAULT 0 CHECK(safety_stock>=0), minimum_stock integer NOT NULL DEFAULT 0 CHECK(minimum_stock>=0),
 PRIMARY KEY(variant_id,warehouse_id)
);
CREATE TABLE inventory_lots (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,variant_id text NOT NULL REFERENCES variants(id),lot_number text NOT NULL,expires_at date,recall_reference text,quarantined boolean NOT NULL DEFAULT false,UNIQUE(variant_id,lot_number));
CREATE TABLE inventory_movements (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,variant_id text NOT NULL REFERENCES variants(id),warehouse_id text NOT NULL REFERENCES warehouses(id),
 type text NOT NULL,quantity integer NOT NULL,quarantine_quantity integer NOT NULL DEFAULT 0,reason text NOT NULL,reference text UNIQUE,actor_id text,lot_id text REFERENCES inventory_lots(id),created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bundle_components (bundle_variant_id text NOT NULL REFERENCES variants(id),component_variant_id text NOT NULL REFERENCES variants(id),quantity integer NOT NULL CHECK(quantity>0),CHECK(bundle_variant_id<>component_variant_id),PRIMARY KEY(bundle_variant_id,component_variant_id));
CREATE TABLE carts (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,token_hash text NOT NULL UNIQUE,user_id text,currency text NOT NULL DEFAULT 'TRY',created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE cart_items (cart_id text NOT NULL REFERENCES carts(id) ON DELETE CASCADE,variant_id text NOT NULL REFERENCES variants(id),quantity integer NOT NULL CHECK(quantity>0 AND quantity<=99),PRIMARY KEY(cart_id,variant_id));
CREATE TABLE country_rules (
 code text PRIMARY KEY CHECK(length(code)=2),name text NOT NULL,enabled boolean NOT NULL DEFAULT false,
 product_approved boolean NOT NULL DEFAULT false,age_approved boolean NOT NULL DEFAULT false,payment_approved boolean NOT NULL DEFAULT false,shipping_approved boolean NOT NULL DEFAULT false,tax_approved boolean NOT NULL DEFAULT false,legal_approved boolean NOT NULL DEFAULT false,
 shipping_minor bigint CHECK(shipping_minor>=0),currency text NOT NULL DEFAULT 'TRY',delivery_term text NOT NULL DEFAULT 'DAP',restrictions text NOT NULL DEFAULT '',fixture boolean NOT NULL DEFAULT false
);
CREATE TABLE tax_rules (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,country text NOT NULL REFERENCES country_rules(code),product_class text NOT NULL DEFAULT '*',rate_bps integer NOT NULL CHECK(rate_bps>=0 AND rate_bps<=10000),valid_from timestamptz NOT NULL,valid_until timestamptz,fixture boolean NOT NULL DEFAULT false);
CREATE TABLE coupons (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,code text NOT NULL UNIQUE,discount_bps integer NOT NULL CHECK(discount_bps>0 AND discount_bps<=10000),minimum_minor bigint NOT NULL DEFAULT 0,max_uses integer NOT NULL CHECK(max_uses>0),used_count integer NOT NULL DEFAULT 0 CHECK(used_count>=0),minimum_contribution_minor bigint NOT NULL DEFAULT 0,expires_at timestamptz NOT NULL,active boolean NOT NULL DEFAULT true);
CREATE SEQUENCE order_number_seq;
CREATE TABLE orders (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,number text NOT NULL UNIQUE DEFAULT ('SG-' || lpad(nextval('order_number_seq')::text,7,'0')),
 cart_id text NOT NULL REFERENCES carts(id),user_id text,idempotency_key text NOT NULL,request_hash text NOT NULL,tracking_hash text NOT NULL,
 status text NOT NULL DEFAULT 'awaiting_payment',payment_status text NOT NULL DEFAULT 'pending',fulfillment_status text NOT NULL DEFAULT 'unfulfilled',
 currency text NOT NULL,subtotal_minor bigint NOT NULL,discount_minor bigint NOT NULL DEFAULT 0,shipping_minor bigint NOT NULL,tax_minor bigint NOT NULL,total_minor bigint NOT NULL CHECK(total_minor>=0),
 cost_minor bigint NOT NULL DEFAULT 0,fee_minor bigint NOT NULL DEFAULT 0,advertising_minor bigint NOT NULL DEFAULT 0,return_provision_minor bigint NOT NULL DEFAULT 0,
 email text NOT NULL,address jsonb NOT NULL,locale text NOT NULL DEFAULT 'tr',snapshot jsonb NOT NULL,
 expires_at timestamptz NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),UNIQUE(cart_id,idempotency_key)
);
CREATE INDEX orders_user_created ON orders(user_id,created_at DESC);
CREATE TABLE order_items (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL REFERENCES orders(id),variant_id text NOT NULL REFERENCES variants(id),name text NOT NULL,sku text NOT NULL,quantity integer NOT NULL CHECK(quantity>0),unit_minor bigint NOT NULL,cost_minor bigint NOT NULL,discount_minor bigint NOT NULL DEFAULT 0,tax_minor bigint NOT NULL DEFAULT 0,snapshot jsonb NOT NULL,UNIQUE(order_id,variant_id));
CREATE TABLE reservations (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL REFERENCES orders(id),variant_id text NOT NULL REFERENCES variants(id),warehouse_id text NOT NULL REFERENCES warehouses(id),quantity integer NOT NULL CHECK(quantity>0),status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','consumed','released','expired')),expires_at timestamptz NOT NULL,UNIQUE(order_id,variant_id,warehouse_id));
CREATE INDEX reservations_active ON reservations(variant_id,warehouse_id,expires_at) WHERE status='active';
CREATE TABLE payments (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL UNIQUE REFERENCES orders(id),provider text NOT NULL,status text NOT NULL DEFAULT 'pending',provider_reference text UNIQUE,amount_minor bigint NOT NULL,currency text NOT NULL,refunded_minor bigint NOT NULL DEFAULT 0,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE payment_events (id text PRIMARY KEY,payment_id text NOT NULL REFERENCES payments(id),payload_hash text NOT NULL,status text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE order_history (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL REFERENCES orders(id),type text NOT NULL,from_status text,to_status text,actor_id text,details jsonb NOT NULL DEFAULT '{}',created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE shipments (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL REFERENCES orders(id),carrier text NOT NULL,tracking_number text NOT NULL,status text NOT NULL DEFAULT 'shipped',idempotency_key text NOT NULL UNIQUE,cost_minor bigint NOT NULL DEFAULT 0,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(carrier,tracking_number));
CREATE TABLE shipment_items (shipment_id text NOT NULL REFERENCES shipments(id),variant_id text NOT NULL REFERENCES variants(id),quantity integer NOT NULL CHECK(quantity>0),PRIMARY KEY(shipment_id,variant_id));
CREATE TABLE returns (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL REFERENCES orders(id),variant_id text NOT NULL REFERENCES variants(id),quantity integer NOT NULL CHECK(quantity>0),reason text NOT NULL,seal_intact boolean NOT NULL,status text NOT NULL DEFAULT 'requested',decision_reason text,qc_reason text,restocked boolean NOT NULL DEFAULT false,refund_minor bigint NOT NULL DEFAULT 0,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE refunds (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,return_id text NOT NULL UNIQUE REFERENCES returns(id),payment_id text NOT NULL REFERENCES payments(id),amount_minor bigint NOT NULL CHECK(amount_minor>0),status text NOT NULL,provider_reference text,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE invoice_references (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL REFERENCES orders(id),provider text NOT NULL,external_reference text NOT NULL,document_kind text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(provider,external_reference));
CREATE TABLE content_pages (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,slug text NOT NULL,locale text NOT NULL CHECK(locale IN ('tr','en','de','ru','ar')),title text NOT NULL,body text NOT NULL,status text NOT NULL CHECK(status IN ('draft','published')),version integer NOT NULL DEFAULT 1,publish_at timestamptz,updated_at timestamptz NOT NULL DEFAULT now(),UNIQUE(slug,locale));
CREATE TABLE content_revisions (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,page_id text NOT NULL REFERENCES content_pages(id),version integer NOT NULL,title text NOT NULL,body text NOT NULL,actor_id text,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(page_id,version));
CREATE TABLE settings (key text PRIMARY KEY,value jsonb NOT NULL,updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE audit_log (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,actor_id text NOT NULL,action text NOT NULL,resource text NOT NULL,resource_id text,details jsonb NOT NULL DEFAULT '{}',created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE jobs (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,type text NOT NULL,payload jsonb NOT NULL DEFAULT '{}',dedupe_key text NOT NULL UNIQUE,status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed')),attempts integer NOT NULL DEFAULT 0,max_attempts integer NOT NULL DEFAULT 5,available_at timestamptz NOT NULL DEFAULT now(),lease_until timestamptz,last_error text,created_at timestamptz NOT NULL DEFAULT now(),completed_at timestamptz);
CREATE INDEX jobs_claim ON jobs(status,available_at);
CREATE TABLE suppliers (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,name text NOT NULL,lead_days integer NOT NULL DEFAULT 0 CHECK(lead_days>=0),contact_email text,archived boolean NOT NULL DEFAULT false);
CREATE TABLE purchase_orders (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,supplier_id text NOT NULL REFERENCES suppliers(id),status text NOT NULL DEFAULT 'draft',currency text NOT NULL DEFAULT 'TRY',created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE purchase_items (purchase_id text NOT NULL REFERENCES purchase_orders(id),variant_id text NOT NULL REFERENCES variants(id),quantity integer NOT NULL CHECK(quantity>0),received integer NOT NULL DEFAULT 0,unit_cost_minor bigint NOT NULL CHECK(unit_cost_minor>=0),PRIMARY KEY(purchase_id,variant_id));
CREATE TABLE channel_mappings (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,channel text NOT NULL,variant_id text NOT NULL REFERENCES variants(id),external_sku text NOT NULL,price_minor bigint,quota integer NOT NULL DEFAULT 0,safety_stock integer NOT NULL DEFAULT 0,status text NOT NULL DEFAULT 'blocked',last_sync_at timestamptz,UNIQUE(channel,external_sku));
CREATE TABLE import_batches (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,status text NOT NULL DEFAULT 'review',source text NOT NULL,rows jsonb NOT NULL,errors jsonb NOT NULL DEFAULT '[]',actor_id text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE customer_addresses (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,user_id text NOT NULL,label text NOT NULL,address jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE wishlists (user_id text NOT NULL,product_id text NOT NULL REFERENCES products(id),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(user_id,product_id));
CREATE TABLE consent_records (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,user_id text,token_hash text,kind text NOT NULL,granted boolean NOT NULL,version text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
