from django import forms
from django.db import models

class Tag(models.Model):
    """A simple way to organize layers.
    """
    name = models.CharField( max_length = 50 )

class LayerGroup(models.Model):
    """A class for grouping DataLayers.

        Allows for a simple, high-level organization
        separate from Tags.
    """
    name = models.CharField( max_length=200 )
    notes = models.TextField( null=True, blank=True )
    tags = models.ManyToManyField( 'Tag', null=True, blank=True )

class DataLayer(models.Model):
    """A class for dealing with uploads of data.

        has a name, projection, srs (if found),
        and other info to determine how it should be processed.
    """
    name = models.CharField( max_length=200 )
    proj = models.TextField( null=True, blank=True )
    srs = models.CharField( max_length=16, null=True, blank=True )
    notes = models.TextField( null=True, blank=True )
    tags = models.ManyToManyField( 'Tag', null=True, blank=True )
    group = models.ForeignKey( 'LayerGroup', null=True, blank=True )

class FileUpload(models.Model):
    """An uploaded file. Multiple files may make up the contents for one
    DataLayer.
    """
    file = models.FileField(upload_to='uploads/')
    date_added = models.DateTimeField( auto_now_add=True )
    layer = models.ForeignKey( 'DataLayer', null=True, blank=True )

class Attribute(models.Model):
    """Refers to a gis attribute/column/property of a particular layer.
    """
    name = models.CharField( max_length=50 )
    type = models.CharField( max_length=50 )
    layer = models.ForeignKey( 'DataLayer' )

class FileUploadForm( forms.Form ):
    """A form for uploading any kind of data file.

        Used to validate uploads.
    """
    name = forms.CharField(
            max_length=200,
            help_text='The name of the layer this file belongs to.')

    file = forms.FileField(
            help_text='The file to upload.')

    proj = forms.CharField(
            max_length=500,
            help_text='Spatial Reference System text for this layer.')

    srs = forms.CharField(
            max_length=16,
            help_text='SRS or EPSG code of the Spatial Reference System for this layer.')

    notes = forms.CharField(
            required=False,
            help_text='Notes about the layer this file belongs to.')

    tags = forms.CharField(
            required=False,
            max_length=200,
            help_text='Tags for the layer this file belongs to.')


