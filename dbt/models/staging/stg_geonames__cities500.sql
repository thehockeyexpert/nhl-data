-- One row per GeoNames place with at least 500 people (cities500), worldwide. GeoNames, CC BY 4.0.
{{ config(tags=['geonames']) }}

{{ geonames_places('geonames__cities500') }}
