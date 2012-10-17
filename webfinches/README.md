# Webfinches

This is meant to be a pluggable django app for uploading GIS data, and
outputting 3d site models for use in 3d modeling applications.

Basically here are the steps for use:

1. upload GIS data (only shapefiles are supported at this time), name and tag
   your layers.
2. setup a sitemodel scheme, with a 'site' layer and a collection of other
   layers and the GIS attributes you would like them to maintain, and a radius
   for determining how much geometry to include in your site models.
3. Generate site model files, and either download them to your local computer,
   or access them on-demand via the grasshopper webfiches connection component.
4. Use them in Grasshopper.

Other features to come.


## Dependencies

* Requires all the [dependencies of GeoDjango](https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#requirements) ( GEOS, PROJ.4, PostGIS), as well as GDAL.
* expects to run with a PostGIS-enabled database
