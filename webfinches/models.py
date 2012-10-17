import os
import zipfile
from urllib import urlencode
from urllib2 import urlopen
import json

from django import forms
from django.contrib import gis
from django.contrib.auth.models import User
from django.core import validators
from django.contrib.gis.db import models

# requires GeoDjango Libraries
from django.contrib.gis.gdal import DataSource

# the basepath for file uploads (needed to read shapefiles)
from settings import MEDIA_ROOT

def get_upload_path(instance, filename):
    return instance.get_upload_path(filename)

class Authored(models.Model):
    """For things made by people """
    author = models.ForeignKey(User)
    class Meta:
        abstract=True

class Named(models.Model):
    """just putting names on models"""
    name = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        abstract=True

class Dated(models.Model):
    date_added = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)
    class Meta:
        abstract=True

class Noted(models.Model):
    notes = models.TextField(null=True, blank=True)
    class Meta:
        abstract=True

class GeomType(models.Model):
    """adding geomtery type"""
    geometry_type = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        abstract=True

class Bboxes(models.Model):
    """shapefile's bounding box"""
    bbox = models.TextField()
    class Meta:
        abstract=True

class GeomFields(models.Model):
    """adding attribute fields"""
    fields = models.TextField()
    class Meta:
        abstract=True
        
class FilePath(models.Model):
    """adding attribute fields"""
    pathy = models.TextField()
    class Meta:
        abstract=True

class OGRGeom(models.Model):
    """adding attribute fields"""
    ogr_geom = models.GeometryField()
    objects = models.GeoManager()
    class Meta:
        abstract=True

class Lookup(Named):
    """name and slug"""
    slug = models.SlugField(max_length=100, null=True, blank=True)
    class Meta:
        abstract=True

class DataFile(Dated):
    """Data files represent individual file uploads.
    They are used to construct DataLayers.
    """
    file = models.FileField(upload_to=get_upload_path)
    upload = models.ForeignKey('UploadEvent', null=True, blank=True)
    def get_upload_path(self, filename):
        return 'uploads/%s/%s' % (self.upload.user.username, filename)
    def abs_path(self):
        """returns the full path of the zip file"""
        return os.path.join( MEDIA_ROOT, self.file.__unicode__())
    def extract_path(self):
        """returns a directory path for extracting zip files to"""
        return os.path.splitext( self.abs_path() )[0]
    def path_of_part(self, ext):
        """give an file extension of a specific file within the zip file, and
        get an absolute path to the extracted file with that extension.
        Assumes that the contents have been extracted.
        Returns `None` if the file can't be found
        """
        pieces = os.listdir( self.extract_path() )
        piece = [p for p in pieces if ext in p]
        if not piece:
            return None
        else:
            return os.path.join( self.extract_path(), piece[0] )
    def __unicode__(self):
        return "DataFile: %s" % self.file.url
    def get_layer_data(self):
        """extracts relevant data for building LayerData objects
        meant to be used as initial data for LayerReview Forms
        """
        data = {}
        data['data_file_id'] = self.id
        abs_path = self.abs_path()
        # see if we need to extract it
        extract_dir = self.extract_path()
        basename = os.path.split( extract_dir )[1]
        if not os.path.isdir( extract_dir ):
            # extract it to a directory with that name
            os.mkdir( extract_dir )
            zip_file = zipfile.ZipFile( self.file )
            zip_file.extractall( extract_dir )

        # get shape type
        shape_path = self.path_of_part('.shp')
        ds = DataSource( shape_path )
        layer = ds[0]

        data['geometry_type'] = layer.geom_type.name
        data['name'] = layer.name
        data['fields'] = layer.fields
        data['bbox'] = layer.extent.tuple
        data['tags'] = ''
        data['pathy'] = shape_path

        if layer.srs:
            srs = layer.srs
            try:
                srs.identify_epsg()
                data['srs'] = srs['AUTHORITY'] +':'+srs['AUTHORITY', 1]
            except:
                data['srs'] = None
        if not data['srs']:
            # get .prj text
            prj_path = self.path_of_part('.prj')
            if prj_path:
                prj_text = open(prj_path, 'r').read()
                data['notes'] = prj_text
            data['srs'] = 'No known Spatial Reference System'
        return data
    
    def get_srs(self):
        """takes the prj data and sends it to the prj2epsg API.
        The API returns the srs code if found.
        """
    
        api_srs = {}
        prj_path = self.path_of_part('.prj')
        if prj_path:
            prj_text = open(prj_path, 'r').read()
            query = urlencode({
                'exact' : False,
                'error' : True,
                'terms' : prj_text})
            webres = urlopen('http://prj2epsg.org/search.json', query)
            jres = json.loads(webres.read())
            if jres['codes']:
                api_srs['message'] = 'An exact match was found'
                api_srs['srs'] = int(jres['codes'][0]['code'])
            else:
                api_srs['message'] = 'No exact match was found'
                ason_srs['srs'] = 'No known Spatial Reference System'
        return api_srs

    def get_centroids(self, spatial_ref):
        '''
        Gets the centroids of the site layer to do a distance query based on them.
        Converts different type of geometries int point objects.
        '''
        
        shp_path = self.path_of_part('.shp')
        site_ds = DataSource(shp_path)
        site_layer = site_ds[0]
        geoms = [ ]
        for feature in site_layer:
            #Geometries can only be transformed if they have a .prj file
            if feature.geom.srs:
                polygon = feature.geom.transform(spatial_ref,True)
                #Get the centroids to calculate distances.
                if polygon.geom_type == 'POINT':
                    centroids = polygon
                    geoms.append(centroids)
                elif polygon.geom_type == 'POLYGON':
                    centroids = polygon.centroid
                    geoms.append(centroids)
                #Linestrings and geometry collections can't return centroids,
                #so we get the bbox and then the centroid.
                elif polygon.geom_type == 'LINESTRING' or 'MULTIPOINT' or 'MULTILINESTRING' or 'MULTIPOLYGON':
                    bbox = polygon.envelope.wkt
                    centroids = OGRGeometry(bbox).centroid
                    geoms.append(centroids)
        return geoms

class DataLayer(Named, Authored, Dated, Noted, GeomType,FilePath):
    srs = models.CharField(max_length=50, null=True, blank=True)
    files = models.ManyToManyField('DataFile', null=True, blank=True )
    tags = models.CharField(max_length=50, null=True, blank=True)
    objects = models.GeoManager()
    def get_browsing_data(self):
        obj = vars(self)
        tags = self.tag_set.all()
        if tags:
            obj['tags'] = ' '.join( [t.name for t in tags] )
        else:
            obj['tags'] = ''
        return obj
    def __unicode__(self):
        return "DataLayer: %s" % self.name

class UploadEvent(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    def __unicode__(self):
        return "UploadEvent: %s" % self.date

class Tag(Lookup, Dated, Noted):
    layers = models.ManyToManyField(DataLayer)
    def __unicode__(self):
        return "Tag: %s" % self.slug

class Attribute(Named):
    layer = models.ForeignKey(DataLayer)
    data_type = models.CharField(max_length=100)
    def __unicode__(self):
        return "Attribute: %s" % self.name

class SiteConfiguration(Named, Authored, Dated, Noted):
    """A model for storing the different site configurations that someone has
    made. It must have a site_layer that defines the separate sites.
        It can add other layers (these should maybe be ordered with
        django-sortedm2m )
        It has a radius and srs code.
        the srs attribute is defined so that it could be proj or WKT text or an
        EPSG code. It will be used to define the coordinate system for the
        built sites.
        This should maybe be immutable. If something is changed, it should make
        a new instance, so that we always can track down the settings used for
        a particular SiteSet.
    """
    site_layer = models.ForeignKey('DataLayer',
            related_name='siteconfiguration_site')
    other_layers = models.ManyToManyField('DataLayer',
            related_name='siteconfiguration_other',
            null=True, blank=True)
    radius = models.IntegerField( default=1000 )
    srs = models.CharField( max_length=500, null=True, blank=True)
    objects = models.GeoManager()
    
    def __unicode__(self):
        return "SiteConfiguration: %s" % self.name

class SiteSet(Dated, Authored, Named): #I need to add the name of the site configuration!
    """A model for managing a set of generated sites.
        Someone can generate sites more than once from the same
        SiteConfiguration.
        A SiteSet has a set of Sites
    """

    configuration = models.ForeignKey('SiteConfiguration') #just quickly getting something ready for venice.
    geoJson = models.TextField() # if it breaks, I need to get rid of this frome the DB
    
    def __unicode__(self):
        return "SiteConfiguration: %s" % self.name

class Site(models.Model):
    """A model for managing an individual generated Site.
        A Site belongs to a Site Set and has a set of LocalLayers
    """
    site_id = models.IntegerField()
    site_set = models.ForeignKey('SiteSet')

class LocalLayer(models.Model):
    """A model for managing an individual generated layer in an individual
    Site.
        A LocalLayer belongs to a Site.
    """
    site = models.ForeignKey('Site')
    origin_layer = models.ForeignKey('DataLayer')

def create_from_shapefile(self, path):
    ds = DataSource(path)
    layer = ds[0]
    for feature in layer:
        DataLayer.objects.create(geometry=feature['geometry'], field=feature['field'])
        