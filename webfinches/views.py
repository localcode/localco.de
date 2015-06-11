import os
import math
import itertools
from itertools import *
import json
import tempfile, zipfile
import cStringIO
import datetime

from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from webfinches.forms import *
from webfinches.models import *
from django.contrib.auth.views import login
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

import django.contrib.gis
from django.contrib.gis.geos import *
from django.contrib.gis.db import models
from django.contrib.gis.measure import D
from django.contrib.gis.gdal import *

###test

def index(request):
    """A view for browsing the existing webfinches.
    """
    return render_to_response(
            'webfinches/index.html',
            {'webfinches':DataLayer.objects.all()},
            )

@login_required
def upload(request):
    """A view for uploading new data.
    """
    user = request.user
    print request
    if request.method == 'POST':
        upload = UploadEvent(user=user)
        upload.save()
        formset = ZipFormSet(request.POST, request.FILES)
        for form in formset:
            if form.is_valid() and form.has_changed():
                data_file = form.save(upload)
        return HttpResponseRedirect('/webfinches/review/')
    else:
        formset = ZipFormSet()

    c = {
            'formset':formset,
            }
    return render_to_response(
            'webfinches/upload.html',
            RequestContext(request, c),
            )

@login_required
def review(request):
    """
    A view for uploading new data.
    """
    user = request.user
    print 22222
    if request.method == 'POST': # someone is giving us data
        formset = LayerReviewFormSet(request.POST)
        if formset.is_valid():
            # For every layer in the layer form, write a PostGIS object to the DB
            for form in formset:
                '''
                PostGIS DB input
                '''
                if form.cleaned_data['srs'].isnumeric():
                    srs = int(form.cleaned_data['srs'])
                else:
                    srs = int(form.cleaned_data['srs'][form.cleaned_data['srs'].find(':')+1:])
                print 33333333333
                
                # Write the layer to the DB
                loaded_layer = load_layer(form.cleaned_data['pathy'], srs, user)
                #print loaded_layer
                #print loaded_layer.author, loaded_layer.date_added, loaded_layer.geometry_type
                

                
        return HttpResponseRedirect('/webfinches/configure/')

    else: # we are asking them to review data
        # get the last upload of this user
        upload = UploadEvent.objects.filter(user=user).order_by('-date')[0]
        data_files = DataFile.objects.filter(upload=upload)
        layer_data = [ f.get_layer_data() for f in data_files ]
        formset = LayerReviewFormSet( initial=layer_data )
        
    c = {
            'formset':formset,
            }
    return render_to_response(
            'webfinches/review.html',
            RequestContext(request, c),
            )
                    

@login_required
def browse(request):
    """A view for browsing and editing layers"""
    user = request.user
    if request.method == 'POST': # someone is giving us data
        formset = LayerReviewFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data['srs'].isnumeric():
                    srs = int(form.cleaned_data['srs'])
                else:
                    srs = int(form.cleaned_data['srs'][form.cleaned_data['srs'].find(':')+1:])
                # Write the layer to the DB
                loaded_layer = load_layer(form.cleaned_data['pathy'], srs, user)
                
        return HttpResponseRedirect('/webfinches/configure/')

    else:
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        browsing_data = [ l.get_browsing_data() for l in layers ]
        # do I need to convert these to dicts?
        formset = LayerBrowseFormSet(initial=browsing_data)
        all_tags = Tag.objects.all()
    
    c = {
            'formset': formset,
            'tags': all_tags,
            
            }
    return render_to_response(
            'webfinches/browse.html',
            RequestContext( request, c ),
            )

@login_required
def browse_empty(request):
    c = {
            'layers': None,
    
            }
    return render_to_response(
            'webfinches/browse_empty.html',
            RequestContext(request, c),
            )

@login_required
def configure(request):
    """
    A view that contains ajax scripts for sorting and dealing with layers,
    in order to build SiteConfigurations
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        #Here we are getting some user variables
        layers = PostLayerG.objects.filter(author=user).order_by('-date_edited')
        # Get site_layer from checkboxes
        site_id = request.POST.get("site_layer")
        site_layer = PostLayerG.objects.get(id=site_id)
        # We get the SiteConfiguration name entered by the user
        config_name = request.POST.get("name") 
        # Get radius for query
        try:
            radius = int(request.POST.get("radius"))
        except ValueError:
            # We give them a predefined Radius if no radius or an invalid radius is selected
            radius = 1000 
        # We get the SRS code. If the user doesn't provide an srs code, use the site's srs code
        if len(request.POST.get("srs")) == 0: 
            config_srs = site_layer.layer_srs
        elif request.POST.get("srs").isnumeric():
            config_srs = int(request.POST.get("srs"))
        else:
            config_srs = int(request.POST.get("srs")[request.POST.get("srs").find(':')+1:])
                    
        # Get other_layers from checkboxes
        other_ids = request.POST.getlist("other_layers")
        if len(other_ids) > 0:
            other_layers = [PostLayerG.objects.get(id=other_layers_id) for other_layers_id in other_ids]
            # Create a PostSiteConfig with the layers
            configuration = load_configuration(author=user, config_name=config_name, site_layer=site_layer, other_layers=other_layers, config_srs=config_srs, radius=radius)
            print configuration, configuration.site.all()[0].features.all()
            
        else:
            configuration = load_configuration(author=user, config_name=config_name, site_layer=site_layer, config_srs=config_srs, radius=radius)
            print configuration, configuration.site.all()[0].features.all()
            
        
        return HttpResponseRedirect('/webfinches/create_sites/')

    else:
        # We are browsing data
        test_layers = PostLayerG.objects.filter(author=user).order_by('-date_edited')
        
    c = {
            'test_layers': test_layers,
    
            }
    return render_to_response(
            'webfinches/configure.html',
            RequestContext(request, c),
            )

@login_required
def create_sites(request):
    """
    A view to generate sites based on SiteConfigurations and Spatial Database
    Queries
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        site_configurations = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')
        if len(site_configurations)>0:
            # Get the site ID
            configuration_id = request.POST.get("create_sites")
            my_config = PostConfigurationB.objects.filter(id=configuration_id)[0]
            if my_config.config_srs:
                srs = my_config.config_srs
            else: srs = None
            # Set query distance
            distance= my_config.radius
            # Get a list of site geometries
            sites = my_config.site.all()[0].features.all()
            other_layerz = my_config.other_layers.all()
            
            minimum = request.POST.get("min")
            if len(minimum) == 0 or int(minimum)<0:
                minimum = 0
            maximum = request.POST.get("max")
            if len(maximum) == 0 or int(maximum)>len(sites):
                maximum = len(sites)
            print int(minimum), type(minimum)
            print int(maximum), type(maximum)
            
            
            all_geoJSON = []
            for j, my_site in enumerate(sites[int(minimum):int(maximum)]):
                jsons = []
                # Add the site to the geoJSON
                jsons.append(query_to_json([sites[j]], site=True, srs=srs))
                
                # See if other sites are within the site
                other_sites_query = sites.filter(geom__distance_lte=(my_site.geom, D(m=distance)))
                if len(other_sites_query) > 0:
                    jsons.append(query_to_json(other_sites_query, other_sites=True, srs=srs))
                
                # Do queries with other layers
                if len(other_layerz) > 0:
                    for other_layer in other_layerz:
                        # Here I select which geometries get queried... according to layer name in other layers and site configuration
                        query = other_layer.features.all().filter(geom__distance_lte=(my_site.geom, D(m=distance)))
                        #print len(query)
                        if len(query) > 0:
                            # Add other layers to the geoJSON
                            jsons.append(query_to_json(query, srs=srs))
                print jsons
                # Add some other tags to the geoJSON, and transform from a python dict to a geoJSON
                geoJSON = json.dumps({"layers":jsons, "type":"LayerCollection"})
                #print geoJSON
                all_geoJSON.append(geoJSON)
            
            #Write to ZIP file
            # Create the file object
            zipdata = cStringIO.StringIO()
            # Create the zipfile
            zip_file = zipfile.ZipFile(zipdata, "a") 
            # Get individual jsons from sitesets
            i = int(minimum)-1
            for jason in all_geoJSON: 
                i += 1
                # Write individual txt files into zip file
                zip_file.writestr(str(i) + '.txt',jason) 
            
            zip_file.close()
            zipdata.flush()
            
            # generate the file
            response = HttpResponse(FileWrapper(zipdata), 'rb')
            response['Content-Disposition'] = 'attachment; filename=site_set.zip'
            zipdata.seek(0)
            #zipdata.close() # Deletes the temp file object
            
            return response # Un-comment to get the file download.
        
        else:
            return HttpResponseRedirect('/webfinches/create_sites_empty/')
    
    else:
        # We are browsing data
        test_configurations = PostConfigurationB.objects.filter(author=user).order_by('-date_edited')
        #print test_configurations[0].site.all()[0].layer_name

    c = {
            'test_configurations': test_configurations
            }
    return render_to_response(
            'webfinches/create_sites.html',
            RequestContext(request, c),
            )
    
@login_required
def create_sites_empty(request):
    c = {
            'layers': None,
    
            }
    return render_to_response(
            'webfinches/create_sites_empty.html',
            RequestContext(request, c),
            )

@login_required
def get_sites(request):
    """
    A view to generate sites based on SiteConfigurations and Spatial Database
    Queries. The view get the geoJson files, writes them to a file-object and
    creates a zip file to be dowloaded
    """
    # Might be better to just save the zip files as files on the db and then
    # trigger the dowload?
    
    user = request.user
    # this is where I screw up... I'm getting all the site_sets available!
    # get only the particular ones!
    sites_available = SiteSet.objects.filter(author=user).order_by('-date_edited')
    # this ones give me the date... we can make a list and then compare whatever we
    # had to see if they are part of the site set.
    #print sites_available[0].name[-27:] 
    #print sites_available[24].name[-27:]
    temp_json = [ ]
    for site in sites_available:
        temp_json.append(site.geoJson)
    #y = temp_zip(temp_json)
    #temp_zip(temp_json)
    
    zipdata = cStringIO.StringIO() # Create the file object
    zip_file = zipfile.ZipFile(zipdata, "a") # Create the zipfile
    i = -1
    for json in temp_json: # Get individual jsons from sitesets
        i += 1
        zip_file.writestr(str(i) + '.txt',json) # Write individual txt files into zip file
    zip_file.close()
    zipdata.flush()
    ret_zip = zipdata.getvalue() # Gets the data from the temp file object before deleting it
    #zipdata.close() # Deletes the temp file object
    
    # generate the file
    response = HttpResponse(FileWrapper(zipdata), 'rb')
    response['Content-Disposition'] = 'attachment; filename=site_set.zip'
    zipdata.seek(0)
    #zipdata.close() # Deletes the temp file object
    
    #return response # Un-comment to get the file download.
    # periodical cleanup jobs. Django already has an admin
    # command that must be run periodically to remove old sessions.
    c = {
            'sites_available': sites_available,
            }
    return render_to_response(
            'webfinches/get_sites.html',
            RequestContext(request, c),
            )

"""
This function loads shape files to the DB and serializes their attributes. Every object is an individual geometry
with a dictionary, and a layer that may be converted to a JSON
"""
def load_shp(layer, srs):
    # Get the layer name
    name = layer.name
    # Get the geometry type
    geom_type = layer.geom_type.name
    # Get the GIS fields
    fields = layer.fields
    
    # Get the GEOS geometries from the SHP file
    geoms = layer.get_geoms(geos=True)
    print [geom.centroid[0] for geom in geoms]
    for geom in geoms:
        geom.srid= srs
    # If the geometries are polygons, turn them into linestrings... postGIS query problems
    if geom_type == 'Polygon' or geom_type == 'MultiPolygon':
        geoms = [geom.boundary for geom in geoms]

    shapes = []
    # For every geometry, get their GIS Attributes and save them in a new object.
    for num, geom in enumerate(geoms):
        geom_dict = {}
        # extracrt the GIS field values
        for field in fields:
            geom_dict[str(field)] = str(layer[num].get(field))
        # Saves the dictionary as a str.....
        str_dict = json.dumps(geom_dict)
        # save the object to the DB
        #db_geom = PostGeometries(id_n = num, name = name, srs = srs, atribs = str_dict, geom = geom)
        #db_geom.save()
        #shapes.append(db_geom)
    return shapes


"""
This function loads shape files to the DB and serializes their attributes. Every object is collection of features
with a dictionary as a property.
"""
def load_layer(shp_path, srs, author):
    # Set a GDAL datsource
    ds = DataSource(shp_path)
    layer = ds[0]
    # Get the layer name
    name = layer.name
    geometry_type = layer.geom_type.name
    
    #db_layer = PostLayerG(layer_name=name, layer_srs=srs, author=author, geometry_type=geometry_type)
    #db_layer.save()
    # load the shapes to the db
    shapes = load_shp(layer, srs)
    # For every geometry, get their GIS Attributes and save them in a new object.
    #for shape in shapes:
    #    db_layer.features.add(shape)
    #return db_layer

"""
This function loads site configurations to the DB and relates them to other PostGeom objects as site and other_layers. 
Every object is an individual configuration with a site, site id, srs for transformation, and PostGeom objects.
"""
def load_configuration(author, config_name, site_layer, other_layers=None, radius=1000, config_srs=None):
    if config_srs == None:
        config_srs = site_layer.layer_srs
    
    # Create the configuration db object
    db_config = PostConfigurationB(author=author, config_name=config_name, radius=radius, config_srs=config_srs)
    # Save it to the DB
    db_config.save()
    # Add the site foreign key relationship
    db_config.site.add(site_layer)
    
    # For every other layer in other_layers, add the m2m relationship
    if other_layers:
        for other_layer in other_layers:
            db_config.other_layers.add(other_layer)
    return db_config


"""
This function takes a postgis query, and turns it into a Finches geoJSON
"""
def query_to_json(query, site=False, other_sites=False, srs= None):
    # this will have to change to the configuration srs
    geometries = []
    # for every shape in the query
    for shape in query:
        geometry = shape.geom
        # maybe we will reproject all of them into the site's coordinate system
        if srs:
            geometry = shape.geom.transform(srs, True)
        # get a geoJSON object
        geometry = json.loads(geometry.json)
        # create a blank dictionary
        geom_dict = { }
        # add the geometry to the dict
        geom_dict['geometry'] = geometry
        # add a feature tag to the dict
        geom_dict['type'] = 'Feature'
        # get the GIS attribute dictionary into a single dict entry
        geom_dict['properties'] = eval(shape.atribs)
        # add the dictionary to a list of geometries
        geometries.append(geom_dict)
    # get the name of the layer
    site_name = query[0].name
    # if this is the site layer, name it like that
    if site:
        site_name = 'site'
    # if these are other sites, name them like that
    if other_sites:
        site_name = 'other_sites'
    # create the geoJSON for this layer
    geojson_dict = {"type": "Layer", "name":site_name, "contents":{"type": "Feature Collection", "features":geometries}}
    return geojson_dict

def get_centroids(polygon):
    '''
    Gets the centroid of DataLayers to do a distance query based on them.
    Converts different type of geometries into point objects.
    '''
    centroids = [ ]
    if polygon.geom_type == 'POINT':
        centroid = polygon
        centroids.append(centroid)
    elif polygon.geom_type == 'POLYGON':
        centroid = polygon.centroid
        centroids.append(centroid)
    #Linestrings and geometry collections can't return centroid,
    #so we get the bbox and then the centroid.
    elif polygon.geom_type == 'LINESTRING' or 'MULTIPOINT' or 'MULTILINESTRING' or 'MULTIPOLYGON':
        bbox = polygon.envelope.wkt
        centroid = OGRGeometry(bbox).centroid
        centroids.append(centroid)
    return centroids

def get_centroid(polygon):
    '''
    Gets the centroid of DataLayers to do a distance query based on them.
    Converts different type of geometries into point objects.
    '''
    if polygon.geom_type == 'POINT':
        centroids = polygon
    elif polygon.geom_type == 'POLYGON':
        centroids = polygon.centroid
    #Linestrings and geometry collections can't return centroid,
    #so we get the bbox and then the centroid.
    elif polygon.geom_type == 'LINESTRING' or 'MULTIPOINT' or 'MULTILINESTRING' or 'MULTIPOLYGON':
        bbox = polygon.envelope.wkt
        centroids = OGRGeometry(bbox).centroid
    return centroids
    
def temp_zip(data):
    # Writes a temporary zipfile with any string input and cleans it up afterwards.
    
    zipdata = cStringIO.StringIO() # Create the file object
    zip_file = zipfile.ZipFile(zipdata, "a") # Create the zipfile
    i = -1
    for json in data: # Get individual jsons from sitesets
        i += 1
        zip_file.writestr(str(i) + '.txt',json) # Write individual txt files into zip file
    zip_file.close()
    zipdata.flush()
    ret_zip = zipdata.getvalue() # Gets the data from the temp file object before deleting it
    #zipdata.close() # Deletes the temp file object
    
    # generate the file
    response = HttpResponse(FileWrapper(zipdata), 'rb')
    response['Content-Disposition'] = 'attachment; filename=site_set.zip'
    zipdata.seek(0)
    return response
    

