# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Tag'
        db.create_table('layers_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('layers', ['Tag'])

        # Adding model 'LayerGroup'
        db.create_table('layers_layergroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('layers', ['LayerGroup'])

        # Adding M2M table for field tags on 'LayerGroup'
        db.create_table('layers_layergroup_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('layergroup', models.ForeignKey(orm['layers.layergroup'], null=False)),
            ('tag', models.ForeignKey(orm['layers.tag'], null=False))
        ))
        db.create_unique('layers_layergroup_tags', ['layergroup_id', 'tag_id'])

        # Adding model 'DataLayer'
        db.create_table('layers_datalayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('proj', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('srs', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.LayerGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('layers', ['DataLayer'])

        # Adding M2M table for field tags on 'DataLayer'
        db.create_table('layers_datalayer_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('datalayer', models.ForeignKey(orm['layers.datalayer'], null=False)),
            ('tag', models.ForeignKey(orm['layers.tag'], null=False))
        ))
        db.create_unique('layers_datalayer_tags', ['datalayer_id', 'tag_id'])

        # Adding model 'FileUpload'
        db.create_table('layers_fileupload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.DataLayer'], null=True, blank=True)),
        ))
        db.send_create_signal('layers', ['FileUpload'])

        # Adding model 'Attribute'
        db.create_table('layers_attribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.DataLayer'])),
        ))
        db.send_create_signal('layers', ['Attribute'])


    def backwards(self, orm):
        
        # Deleting model 'Tag'
        db.delete_table('layers_tag')

        # Deleting model 'LayerGroup'
        db.delete_table('layers_layergroup')

        # Removing M2M table for field tags on 'LayerGroup'
        db.delete_table('layers_layergroup_tags')

        # Deleting model 'DataLayer'
        db.delete_table('layers_datalayer')

        # Removing M2M table for field tags on 'DataLayer'
        db.delete_table('layers_datalayer_tags')

        # Deleting model 'FileUpload'
        db.delete_table('layers_fileupload')

        # Deleting model 'Attribute'
        db.delete_table('layers_attribute')


    models = {
        'layers.attribute': {
            'Meta': {'object_name': 'Attribute'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['layers.DataLayer']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'layers.datalayer': {
            'Meta': {'object_name': 'DataLayer'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['layers.LayerGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'proj': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'srs': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['layers.Tag']", 'null': 'True', 'blank': 'True'})
        },
        'layers.fileupload': {
            'Meta': {'object_name': 'FileUpload'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['layers.DataLayer']", 'null': 'True', 'blank': 'True'})
        },
        'layers.layergroup': {
            'Meta': {'object_name': 'LayerGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['layers.Tag']", 'null': 'True', 'blank': 'True'})
        },
        'layers.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['layers']
