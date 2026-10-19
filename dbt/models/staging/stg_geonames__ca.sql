-- One row per GeoNames feature in Canada: places of any size, neighbourhoods, former municipalities, and also lakes,
-- hills and other features (feature_class tells them apart). GeoNames, CC BY 4.0.
{{ config(tags=['geonames']) }}

{{ geonames_places('geonames__ca') }}
