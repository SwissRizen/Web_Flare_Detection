import os,sys, subprocess

import streamlit as st
import sqlite3 as sq

import statistics as stat

import astropy.units as u

import matplotlib.pyplot as plt
import matplotlib.colors as colors

import numpy as np

import sunpy
import sunpy.map as smap
import sunpy.data.sample
import sunpy.coordinates


from sunpy.physics.solar_rotation import mapsequence_solar_derotate
from sunpy.net import Fido, attrs as a
from datetime import datetime, timedelta, date


@st.cache(show_spinner=True,suppress_st_warning=True)
def Flarefinder(start_datetime, end_datetime):
    instrument = a.Instrument('AIA')
    wave = a.Wavelength(13*u.nm, 14*u.nm)


    start_datetime_d = start_datetime + timedelta(seconds=15)
    end_datetime_d = end_datetime + timedelta(seconds=15)
    result = Fido.search(a.Time(start_datetime, start_datetime_d) | a.Time(end_datetime, end_datetime_d) , instrument, wave)
    downloaded_files = Fido.fetch(result, path="C:/Users/Nils/Documents/MaTa/flaskandst/sunpymaps")
    maps = smap.Map(downloaded_files, sequence = True)
    maps = mapsequence_solar_derotate(maps)
    amount = len(maps)

    #%%######################################################################-Superpixel-######################################################################
    pixamt = 128
    newdim1= u.Quantity(maps[0].dimensions)/pixamt
    newdim2 = u.Quantity(maps[amount-1].dimensions)/pixamt
    spmap1 = maps[0].superpixel(newdim1)
    spmap2 = maps[amount-1].superpixel(newdim2)

    #%%######################################################################-Difference Map-######################################################################

    diff = spmap1.data - spmap2.data
    metadiff= spmap2.meta
    diffmap= smap.Map(diff,metadiff)
    #vdef = diffmap.max()*0.6
    #fig = plt.figure()
    #ax_diffmap= plt.subplot(projection = diffmap)
    #dplot = diffmap.plot(cmap='Greys_r', norm=colors.Normalize(vmin=-vdef, vmax=vdef))
    #st.write(fig)

    #%%#####################################################################-Flare Detection Procedure-########################################################################

    bar = diffmap.max()*0.99

    pixelpos = np.argwhere(abs(diffmap.data) >= bar)*u.pixel
    if len(pixelpos) == 0:
        print('no flares found')

    else:
        print('Possible flare locations:')
        print(pixelpos)
        print('Keep in mind here in pixel format it is y,x and not x,y')
        
    pixelcord = diffmap.pixel_to_world(pixelpos[:,1], pixelpos[:,0])
    print(pixelcord)

    #%%#####################################################################-Submap-########################################################################

    pixoperator = (540, 960)*u.pixel
    pixelpos4k = pixelpos * (4096/pixamt)
    PPLEN = len(pixelpos)

    



    x= 0
    while x < PPLEN:
        now = datetime.utcnow()
        nowstr = now.strftime("%Y%b%athe%d%H%M%S")
        startstr = start_datetime.strftime("%Y%b%athe%d%H%M%S")
        endstr = end_datetime.strftime("%Y%b%athe%d%H%M%S")
        pixbot = pixelpos4k[x] - pixoperator
        cordbot = maps[amount-1].pixel_to_world(pixbot[1], pixbot[0])
        submap = maps[amount-1].submap(cordbot, width=1153.43016*u.arcsec, height=648.75384*u.arcsec)
        fig = plt.figure()
        ax_submap = plt.subplot(projection = submap)
        submap.plot(cmap='sdoaia131')
        urlstr = "static/Submaps/" + nowstr + "_" + startstr + "_" + endstr + ".jpeg"
        plt.savefig(urlstr)
        
        newflare = [startstr, endstr, urlstr]
        conn.execute('''insert into flares(stime, etime, urlfor) values (?,?,?) ''', newflare)
        conn.commit()
        st.write(fig)
        x += 1
    
   
       
st.title("Flare Detection WebApp")
st.write("if it works it works")
today = date.today()
tmrw = today + timedelta(days=1)

start_date = st.sidebar.date_input('Start date')
start_time = st.sidebar.time_input('Start time')
end_date = st.sidebar.date_input('End date')
end_time = st.sidebar.time_input('End time')

if start_date <= end_date:
    if start_time < end_time:
        st.success('Ready to go!')
    else:
        st.error('Error: End time must fall after start time')
else:
    st.error('Error: End date must fall after or equal start date.')
    


global start_datetime, end_datetime 
start_datetime = datetime.combine(start_date,start_time)
end_datetime = datetime.combine(end_date,end_time)

st.write('Start Datetime: `%s`\n\nEnd Datetime:`%s`' % (start_datetime, end_datetime))


if st.sidebar.button('TEST'):
    st.write('IT WORKED')
    Flarefinder(start_datetime, end_datetime)
else: st.write('NOT LOADED YET')