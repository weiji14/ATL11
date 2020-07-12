#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 09:52:39 2020

@author: root

NOTE: Requires the presence of atl11_metadata_template.h5 in same directory as this python file!
"""
import os, h5py
import numpy as np
import sys
from datetime import datetime
import ATL11
from ATL11.h5util import create_attribute
from ATL11.version import version

def write_METADATA(outfile,infiles):
    if os.path.isfile(outfile):        
#
# Call filemeta, copies METADATA grouop from template
#
        filemeta(outfile,infiles)
        g = h5py.File(outfile,'r+')
#        g.create_group('METADATA')
#        gl = g['METADATA'].create_group('Lineage')
#        gf = gl.create_group('ATL06')
        gf = g.create_group('METADATA/Lineage/ATL06')
        fname = []
        sname = []
        scycle = []
        ecycle = []
        srgt = []
        ergt = []
        sregion = []
        eregion = []
        sgeoseg = []
        egeoseg = []
        sorbit = []
        eorbit = []
        uuid = []
        version = []
        for ii,infile in enumerate(sorted(infiles)):
            fname.append(os.path.basename(infile).encode('ASCII'))
            if os.path.isfile(infile):
                f = h5py.File(infile,'r')
# Read the datasets from ATL06 ancillary_data, where available
# All fields must be arrays, not just min/max, even if just repeats
#
                sname.append(f['/'].attrs['short_name'])
                uuid.append(f['/'].attrs['identifier_file_uuid'])
                scycle.append(f['ancillary_data/start_cycle'])
                ecycle.append(f['ancillary_data/end_cycle'])
                sorbit.append(f['ancillary_data/start_orbit'])
                eorbit.append(f['ancillary_data/end_orbit'])
                sregion.append(f['ancillary_data/start_region'])
                eregion.append(f['ancillary_data/end_region'])
                srgt.append(f['ancillary_data/start_rgt'])
                ergt.append(f['ancillary_data/end_rgt'])
                version.append(f['ancillary_data/version'])
#            version.append(str(digits[2]).encode('ASCII'))
        for pt in g.keys():
            if pt.startswith('pt'):
                sgeoseg = np.min([sgeoseg,np.min(g[pt]['ref_pt'][:])])
                egeoseg = np.max([egeoseg,np.max(g[pt]['ref_pt'][:])])

        gf.attrs['description'] = 'ICESat-2 ATLAS Land Ice'
#
# Use create_attribute for strings to get ASCII and NULLTERM
#
        create_attribute(gf.id, 'fileName', [2], fname)
        create_attribute(gf.id, 'shortName', [2], sname)
        
        gf.attrs['start_orbit'] = np.ravel(sorbit)
        gf.attrs['end_orbit'] = np.ravel(eorbit)
        
        gf.attrs['start_cycle'] = np.ravel(scycle)
        gf.attrs['end_cycle']   = np.ravel(ecycle)
        
        gf.attrs['start_rgt'] = np.ravel(srgt)
        gf.attrs['end_rgt']   = np.ravel(ergt)

        gf.attrs['start_region'] = np.ravel(sregion)
        gf.attrs['end_region'] = np.ravel(eregion)
        
        gf.attrs['start_geoseg'] = np.repeat(sgeoseg,np.size(sregion))
        gf.attrs['end_geoseg'] = np.repeat(egeoseg,np.size(sregion))
                
        create_attribute(gf.id, 'uuid', [2], uuid)
        gf.attrs['version'] = np.ravel(version)

        g.close()
    return outfile    
    
#if __name__=='__main__':
#    outfile = write_METADATA(outfile,infiles)
    
    

def filemeta(outfile,infiles):

#    atl11_info={'Conventions':'', 'citation':'', 'contributor_name':'', 'contributor_role':'', \
#        'creator_name':'', 'data_rate':'',
    orbit_info={'crossing_time':0., 'cycle_number':0, 'lan':0., \
        'orbit_number':0., 'rgt':0, 'sc_orient':0, 'sc_orient_time':0.}
    root_info={'date_created':'', 'geospatial_lat_max':0., 'geospatial_lat_min':0., \
        'geospatial_lon_max':0., 'geospatial_lon_min':0., 'hdfversion':'', 'history':'', \
        'identifier_file_uuid':'', 'identifier_product_format_version':'', 'time_coverage_duration':0., \
        'time_coverage_end':'', 'time_coverage_start':''}
    # copy METADATA group from ATL11 template. Make lineage/cycle_array conatining each ATL06 file, where the ATL06 filenames
    if os.path.isfile(outfile):
        g = h5py.File(outfile,'r+')
        for ii,infile in enumerate(sorted(infiles)):
            m = h5py.File(os.path.dirname(os.path.realpath(__file__))+'/atl11_metadata_template.h5','r')
            if ii==0:
              if 'METADATA' in list(g['/'].keys()):
                  del g['METADATA']
              # get all METADATA groups except Lineage, which we set to zero
              m.copy('METADATA',g)
              if 'Lineage' in list(g['METADATA'].keys()):
                  del g['METADATA']['Lineage']
              g['METADATA'].create_group('Lineage'.encode('ASCII','replace'))
              gf = g['METADATA']['Lineage'].create_group('ANC36-11'.encode('ASCII','replace'))
              gf = g['METADATA']['Lineage'].create_group('ANC38-11'.encode('ASCII','replace'))

              if os.path.isfile(infile):
                f = h5py.File(infile,'r')
                val=' '.join(sys.argv)
                create_attribute(g['METADATA/ProcessStep/PGE'].id, 'runTimeParameters', [], val)
                if ii==0:
                    start_delta_time = f['ancillary_data/start_delta_time'][0]
                    for key, keyval in root_info.items():
                       dsname=key
                       if key=='date_created' or key=='history':
                           val=str(datetime.now().date())
                           val=val+'T'+str(datetime.now().time())
                           create_attribute(g.id, key, [], val)
                           create_attribute(g['METADATA/ProcessStep/PGE'].id, 'stepDateTime', [], val)
                           continue
                       if key=='identifier_product_format_version':
                           val=version()
                           create_attribute(g.id, key, [], val)
                           create_attribute(g['METADATA/ProcessStep/PGE'].id, 'softwareVersion', [], val)
                           continue
                       if key=='time_coverage_start':
                           val = f.attrs[key].decode()
                           create_attribute(g.id, key, [], val)
                           continue
                       if key=='time_coverage_end' or key=='time_coverage_duration':
                           continue
                       if dsname in f.attrs:
                           if isinstance(keyval,float):
                             val = f.attrs[key]
                             g.attrs[key]=val
                           else:
#                             val = f.attrs[key].astype('U13')
                             val = f.attrs[key].decode()
                             create_attribute(g.id, key, [], val)
                    del g['METADATA/Extent']
                    f.copy('METADATA/Extent',g['METADATA'])
                    f.copy('ancillary_data',g)
                    del g['ancillary_data/land_ice']

#
# Read the datasets from orbit_info
#
# BPJ: The orbit info add on doesn't work with "processed_*" files
### Why segfault?                    f.copy('orbit_info',g)
# NOTE: Comment out the 1 following line if using subset files from NSIDC!
                    gf = f.copy('orbit_info',g)
#                    for key, keyval in orbit_info.items():
#                        dsname='/orbit_info/'+key
#                        if dsname in f:
#                           f.copy(dsname,gf)
#                           if f[dsname].dtype.kind == 'S':
#                               orbit_info[key] = (f[dsname][0].decode()).strip()
#                           else:
#                               orbit_info[key] = f[dsname][0]

                m.close()
                f.close()


            if ii==len(infiles)-1:
              if os.path.isfile(infile):
                f = h5py.File(infile,'r')
                for key, keyval in root_info.items():
                    dsname=key
                    if key=='time_coverage_end':
                       val = f.attrs[key].decode()
                       create_attribute(g.id, key, [], val)
                       continue
                    if key=='time_coverage_duration':
                       end_delta_time = f['ancillary_data/end_delta_time'][0]
                       val = float(end_delta_time) - float(start_delta_time)
                       g.attrs[key] = val
#                           create_attribute(g.id, key, [], np.string(val))
                  
                m.close()
                f.close()

        g.close()
        return()

