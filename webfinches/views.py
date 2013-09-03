import os
import math
import itertools
from itertools import *
import json
import tempfile, zipfile
import cStringIO

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
    """A view for uploading new data.
    """
    user = request.user
    if request.method == 'POST': # someone is giving us data
        formset = LayerReviewFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
            # get the DataFile id from the form data
                data_file_id = form.cleaned_data['data_file_id']
                # now get the actual object associated with that id
                data_file = DataFile.objects.get(id=data_file_id)
                srs = form.cleaned_data['srs']
                tags = form.cleaned_data['tags']
                layer = DataLayer(srs = srs, tags=tags)
                layer = form.save(commit=False)
                layer.author = user
                # the DataLayer must exist before we can add relations to it
                layer.save()
                layer.files.add(data_file) # add the relation
                layer.save() # resave the layer
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
    #Maybe we hould add Ajax to the add tags???
    user = request.user
    if request.method == 'POST': # someone is giving us data
        '''
        formset = LayerBrowseFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                # get the DataFile id from the form data
                data_tags = form.cleaned_data['tags']
                # now get the actual object associated with that id
                data_file = DataFile.objects.get(id=data_tags)
                '''
        formset = LayerReviewFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
            # get the DataFile id from the form data
                data_file_id = form.cleaned_data['data_file_id']
                # now get the actual object associated with that id
                data_file = DataFile.objects.get(id=data_file_id)
                
                tags = form.cleaned_data['tags']
                layer = DataLayer(tags = tags)
                layer = form.save(commit=False)
                layer.author = user
                # the DataLayer must exist before we can add relations to its
                layer.save()
                layer.files.add(data_file) # add the relation
                layer.save() # resave the layer
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
def configure(request):
    """A view that contains ajax scripts for sorting and dealing with layers,
        in order to build SiteConfigurations
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        # Get site_layer from checkboxes
        site_id = request.POST.get("site_layer")
        site_layer = DataLayer.objects.get(id=site_id)
        # Get other_layers from checkboxes
        other_ids = request.POST.getlist("other_layers")
        other_layers = [ ]
        for other_layers_id in other_ids:
            other_layers.append(DataLayer.objects.get(id=other_layers_id))
        # Get radius for query
        try:
            radius = int(request.POST.get("radius"))
        except ValueError:
            radius = 1000 # We give them a predefined Radius if no radius or an invalid radius is selected
        srs = request.POST.get("srs") # Get the srs value to reproject DataLayers
        name = request.POST.get("name") # We get the SiteConfiguration name entered by the user
        configuration = SiteConfiguration(srs = srs, radius=radius, site_layer = site_layer
                                          , author = user, name = name)
        configuration.save() # We create the object
        # We add the m2m relationship with other_layes
        for other_layer in other_layers:
            configuration.other_layers.add(other_layer)
        configuration.save() # Re-save the SiteConfiguration
        
        return HttpResponseRedirect('/webfinches/create_sites/')

    else:
        # We are browsing data
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        layer = DataLayer.objects.filter(author=user)[0]
        all_tags = Tag.objects.all()
    
    c = {
            'layers': layers,
            'tags': all_tags,
    
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
        #site_sets = ''
        configuration_id = request.POST.get("create_sites")
        
        # This gives us the selected site and perform distance queries.
        site_configurations_selected = SiteConfiguration.objects.get(id=configuration_id)
        srs = site_configurations_selected.srs
        radius = site_configurations_selected.radius #*10
        
        site_layer = site_configurations_selected.site_layer
        other_layers = site_configurations_selected.other_layers.all()
        path_site_layer = site_layer.get_browsing_data()['pathy']
        ds_site_layer = DataSource( path_site_layer )
        layer_site_layer = ds_site_layer[0]
        
        layer_site_fields = layer_site_layer.fields
        site_field_values = [[geom.get(field) for field in layer_site_fields] for geom in layer_site_layer]
        field_attributes = [dict(itertools.izip(layer_site_fields, field_value)) for field_value in site_field_values]
        site_centroids = [ ]
        site_json = [ ]
        site_dicts = [ ]
        for feature in layer_site_layer:
            if feature.geom.srs:
                polygon = feature.geom.transform(srs,True)
                site_json.append(json.loads(polygon.json))
                #print feature.geom.srs['UNIT']
                # it used to be append(feature.geom.json)
                # but I think this gets the reprojected geom?
                #Get the centroid to calculate distances.
                site_centroids.append(get_centroid(polygon)) 
                # geos testing
                #site_centroids.append(feature.geom.geos)
                
        site_json_dicts = [ ]
        site_num = -1
        for geom in site_json:
            geom_json_dicts = { }
            site_num += 1
            geom_json_dicts['geometry'] = geom
            geom_json_dicts['type'] = 'Feature'
            geom_json_dicts['properties'] = field_attributes[site_num]
            site_json_dicts.append(geom_json_dicts)
        for site_json_dictionary in site_json_dicts:
            site_geojson_dict = {"type": "FeatureCollection", "features":[ ]}
            site_geojson_dict['features'].append( site_json_dictionary )
            site_dict = {"type": "Layer", "name":"site", "contents":site_geojson_dict}
            site_dicts.append(site_dict)
        ##################################
        # maybe I don't need to get the centroid, I can do queries with polygons?
        
        # I also need to add something to be able to add other_sites... sites close to site layer!!!
        
        def get_geo_json(site_dicts, site_centroids, site_number, other_layers):
            site_geojson = site_dicts[site_number]
            site = site_centroids[site_number]
            if len(other_layers) != 0: # if there are multiple layers in the siteConfiguration, iterate through them.
                other_layers_query = [ ]
                for other_layer in other_layers:
                    path_other_layer = other_layer.get_browsing_data()['pathy']
                    ds_site_layer = DataSource( path_other_layer )
                    layer_other_layer = ds_site_layer[0]
                    other_layers_features = [ ]
                    
                    features_dict = {}
                    for feature in layer_other_layer:
                        #Geometries can only be transformed if they have a .prj file
                        
                        ###################################
                        # I think I can use this to convert the units!!!!
                        # just make a quick table of conversions...! and a dict.
                        #print feature.geom.srs['UNIT']
                        # something like if unit == Meter or Metre or METER or METRE or meters or metres
                        # The geos API doesn't transform a global or spherical coordinate system such as
                        # latitude-longitude. These are often referred to as geographic coordinate systems.: ie degrees...
                        # so I need to use the old method and use a conversion to transform distances between those units
                        # Only used Projected Coordinate Systems
                        if feature.geom.srs:
                            polygon = feature.geom.transform(srs,True)
                            #Get the centroid to calculate distances and creates a dictionary with centroids as keys, features as vals
                            features_dict[get_centroid(polygon)] = feature
                            # Geos testing
                            #features_dict[feature.geom.geos] = feature
                    
                    other_centroids = features_dict.keys()
                    for centroid in other_centroids:
                        # Maybe instead of doing this dist query I can turn them into GEOS geom and do distance queries, now that I have dicts.
                        distance = math.sqrt(((site.x-centroid.x)**2)+((site.y-centroid.y)**2))
                        # This is me testing the geos API, but I need to
                        # make sure all the projections are in meters instead!
                        # since I have to reference the base unit before converting....
                        # distance = D(m=g1.distance(g2)).mi
                        #distance = site.distance(centroid) # un comment to test
                        if distance <= radius:
                            print distance
                            other_layers_features.append(features_dict[centroid])
                    other_layers_query.append(other_layers_features)
                    
                # Create dictionaries with the GDAL API
                other_layers_dicts = [ ]
                if len(other_layers_query) > 0:
                    layers_json = [ ]
                    for other_layers in other_layers_query:
                        if len(other_layers)>0:
                            other_layer_name = other_layers[0].layer_name
                            fields = other_layers[0].fields
                            other_field_values = [[geom.get(field) for field in fields] for geom in other_layers]
                            other_field_attributes = [dict(itertools.izip(fields, field_value)) for field_value in other_field_values]
                            other_json = [ ]
                            for feature in other_layers:
                                if feature.geom.srs:
                                    polygon = feature.geom.transform(srs,True)
                                    other_json.append(json.loads(polygon.json))
                            
                            other_json_dict = [ ]
                            other_num = -1
                            for geom in other_json:
                                geom_other = { }
                                other_num += 1
                                geom_other['geometry'] = geom
                                geom_other['type'] = 'Feature'
                                geom_other['properties'] = other_field_attributes[other_num]
                                other_json_dict.append(geom_other)
                            
                            other_geojson_dict = {"type": "Feature Collection", "features":other_json_dict}
                            other_dict = {"type": "Layer", "name":other_layer_name, "contents":other_geojson_dict}
                            layers_json.append(other_dict)
                            
                    '''
                    # this gets the number of geometries per site. 
                    totals = [ ]
                    for i in layers_json:
                        if len(layers_json) == 1:
                            totals.append(len(i['contents']['features']))
                            #print len(i['contents']['features'])
                        else:
                            totals.append(len(i['contents']['features']))
                    print sum(totals)
                    '''
                    layers_json.insert(0, site_geojson) # Add the site_geoJson to the layers
                    geoJSON = {"layers":layers_json, "type":"LayerCollection"}
                    return geoJSON
                
        if len(other_layers) > 0:
            i = 0
            temp_json = [ ]
            for i in range(len(site_centroids)):
                geoJSON = get_geo_json(site_dicts, site_centroids, i, other_layers)
                final_geoJSON = json.dumps(geoJSON)
                #print final_geoJSON
                
                temp_json.append(final_geoJSON)
                
                # Save SiteSets depracated?
                '''
                i += 1
                # Save SitSets
                sites_sets = SiteSet(author = user, configuration = site_configurations_selected,
                                    geoJson = final_geoJSON, name = str(site_configurations_selected.name) + ' / ' + str(i)
                                    + ' / ' + str(site_configurations_selected.date_added))
                sites_sets.save() # We create the object'''
                
            zipdata = cStringIO.StringIO() # Create the file object
            zip_file = zipfile.ZipFile(zipdata, "a") # Create the zipfile
            i = -1
            for jason in temp_json: # Get individual jsons from sitesets
                i += 1
                zip_file.writestr(str(i) + '.txt',jason) # Write individual txt files into zip file
            zip_file.close()
            zipdata.flush()
            
            # generate the file
            response = HttpResponse(FileWrapper(zipdata), 'rb')
            response['Content-Disposition'] = 'attachment; filename=site_set.zip'
            zipdata.seek(0)
            #zipdata.close() # Deletes the temp file object
            
            return response # Un-comment to get the file download.'''
            
                # once I save this as a string, am I gonna be able to
                # access them as a list??? Do I need to save them as m2m????
                # add the m2m relationship with other_layers
                # maybe I can save a list of siteset appending them individually like othe_layers
                # but this needs to be m2m....
                # maybe I have to generate all the site_dicts when I created the site_config and
                # then just retrieve the selected one???
                # for other_layer in other_layers:
                #    configuration.other_layers.add(other_layer)
                
            # From previous version....
            #return HttpResponseRedirect('/webfinches/get_sites/')
            
        else: # if there's only a site layer and no other_layers, create a geoJSON dict for a single layer.
            i = 0
            temp_json = [ ]
            for site in site_dicts:
                geoJSON = {"layers":[site], "type":"LayerCollection"}
                final_geoJSON = json.dumps(geoJSON)
                print final_geoJSON
                temp_json.append(final_geoJSON)
                
                # Save SiteSets depracated?
                '''
                i += 1
                sites_sets = SiteSet(author = user, configuration = site_configurations_selected,
                                    geoJson = final_geoJSON, name = str(site_configurations_selected.name) + ' / ' + str(i)
                                    + ' / ' + str(site_configurations_selected.date_added))
                sites_sets.save() # We create the object'''
            
            zipdata = cStringIO.StringIO() # Create the file object
            zip_file = zipfile.ZipFile(zipdata, "a") # Create the zipfile
            i = -1
            for jason in temp_json: # Get individual jsons from sitesets
                i += 1
                zip_file.writestr(str(i) + '.txt',jason) # Write individual txt files into zip file
            zip_file.close()
            zipdata.flush()
            
            # generate the file
            response = HttpResponse(FileWrapper(zipdata), 'rb')
            response['Content-Disposition'] = 'attachment; filename=site_set.zip'
            zipdata.seek(0)
            #zipdata.close() # Deletes the temp file object
            
            return response # Un-comment to get the file download.'''
            print temp_json
            
            # From previous version....
            #return HttpResponseRedirect('/webfinches/get_sites/')
            # Now I need to add a way to add other sites within range to site set
    
    else:
        # We are browsing data
        site_configurations = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')

    c = {
            'site_configurations': site_configurations,
            }
    return render_to_response(
            'webfinches/create_sites.html',
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
    print sites_available[0].name[-27:] 
    print sites_available[24].name[-27:]
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

@login_required
def download(request):
    #A view for downloading data.
    # configure site layers
    #layers = DataLayer.objects.all()
    #layers = layers
    
    c = {
            'individual_sites': individual_sites,
            'zip_file': zip_file,
            'api_download': api_download,
            #'user': request.User,
            }

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
    

