-- The key used to look up a metric kind should be unique.
ALTER TABLE kpi_metrickind MODIFY code varchar(255) NOT NULL UNIQUE;

-- Drop old non-unique index:
ALTER TABLE kpi_metrickind DROP KEY kpi_metrickind_65da3d2c;
