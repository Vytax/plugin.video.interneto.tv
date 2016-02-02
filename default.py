#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import urllib
import urlparse

import xbmcgui
import xbmcplugin
import xbmcaddon

from libinternetotv import InternetoTV

PLUGIN_ID = 'plugin.video.interneto.tv'

settings = xbmcaddon.Addon(id=PLUGIN_ID)

try:
  import StorageServer
except:
  import storageserverdummy as StorageServer

cache = StorageServer.StorageServer(PLUGIN_ID, 1)


def getParameters(parameterString):
  commands = {}
  splitCommands = parameterString[parameterString.find('?') + 1:].split('&')
  for command in splitCommands:
    if (len(command) > 0):
      splitCommand = command.split('=')
      key = splitCommand[0]
      value = splitCommand[1]
      commands[key] = value
  return commands 

def getChannels():
  return iTV.getChannels()

def build_main_directory():
  
  channels = cache.cacheFunction(getChannels)
  
  for channel in channels:
    
    listitem = xbmcgui.ListItem(channel['title'])
    listitem.setProperty('IsPlayable', 'true')
    listitem.setArt({'thumb' : channel['icon']});
    u = {}
    u['mode'] = 1
    u['url'] = channel['id']
    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = sys.argv[0] + '?' + urllib.urlencode(u), listitem = listitem, isFolder = False, totalItems = 0)
  
  listitem = xbmcgui.ListItem('[ TV įrašai ]')
  listitem.setProperty('IsPlayable', 'False')
  xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = sys.argv[0] + '?mode=2', listitem = listitem, isFolder = True, totalItems = 0)
  
  xbmcplugin.setContent(int( sys.argv[1] ), 'tvshows')
  xbmc.executebuiltin('Container.SetViewMode(515)')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getVideoCats():
  return iTV.getVideoCats()

def build_archive_dir():
  
  videoCats = cache.cacheFunction(getVideoCats)
  
  for videoCat in videoCats:
    
    listitem = xbmcgui.ListItem( videoCat['title'])
    listitem.setProperty('IsPlayable', 'false')
    u = {}
    u['mode'] = 3
    u['url'] = videoCat['id']
    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = sys.argv[0] + '?' + urllib.urlencode(u), listitem = listitem, isFolder = True, totalItems = 0)
    
  xbmcplugin.setContent(int( sys.argv[1] ), 'tvshows')
  xbmc.executebuiltin('Container.SetViewMode(515)')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def build_cat_dir(url):
  
  videos = iTV.getVideoCat(url)
  
  for video in videos:
    
    listitem = xbmcgui.ListItem(video['title'])
    listitem.setProperty('IsPlayable', 'true')
    listitem.setArt({'thumb' : video['image']});
    listitem.setInfo(type = 'video', infoLabels = {'aired': video['date']} )
    u = {}
    u['mode'] = 4
    u['url'] = video['url']
    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = sys.argv[0] + '?' + urllib.urlencode(u), listitem = listitem, isFolder = False, totalItems = 0)

  xbmcplugin.setContent(int( sys.argv[1] ), 'tvshows')
  xbmc.executebuiltin('Container.SetViewMode(515)')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def play_channel(url):
  
  checkCookie()
  data = iTV.getChannelUrls(url)
  if 'login_failed' in data:
    dropCookie()
    checkCookie()
    data = iTV.getChannelUrls(url)
    
  if 'login_failed' in data:
    dialog = xbmcgui.Dialog()
    ok = dialog.ok( "Interneto.TV" , 'Neteisingi prisijungimo duomenys!' )
    return
  
  if not data:
    dialog = xbmcgui.Dialog()
    ok = dialog.ok( "Interneto.TV" , 'Nepavyko paleisti vaizdo įrašo!' )
    return
  
  if 'error' in data:
    dialog = xbmcgui.Dialog()
    ok = dialog.ok( "Interneto.TV" , data['error'] )
    return
  
  listitem = xbmcgui.ListItem(label = data['title'])
  listitem.setPath(data['mp4_hls'].replace('playlist.m3u?', 'playlist.m3u8?'))
  if 'img' in data:
    listitem.setArt({'thumb' : data['img']});
  xbmcplugin.setResolvedUrl(handle = int(sys.argv[1]), succeeded = True, listitem = listitem)

def play_video(url):
  
  checkCookie()
  data = iTV.getVideoURL(url)
  
  if 'login_failed' in data:
    dropCookie()
    checkCookie()
    data = iTV.getVideoURL(url)
    
  if 'login_failed' in data:
    dialog = xbmcgui.Dialog()
    ok = dialog.ok( "Interneto.TV" , 'Neteisingi prisijungimo duomenys!' )
    return
  
  if not data:
    dialog = xbmcgui.Dialog()
    ok = dialog.ok( "Interneto.TV" , 'Nepavyko paleisti vaizdo įrašo!' )
    return
  
  listitem = xbmcgui.ListItem(label = data['title'])
  listitem.setPath(data['mp4_hls'].replace('playlist.m3u?', 'playlist.m3u8?'))
  if 'img' in data:
    listitem.setArt({'thumb' : data['img']});
  xbmcplugin.setResolvedUrl(handle = int(sys.argv[1]), succeeded = True, listitem = listitem)

def getCookie():  
  return iTV.getCookie()

def checkCookie():
  c = dict(urlparse.parse_qsl(cache.get('cookie')))

  if (not c) or (c['email']!=email) or (c['password']!=password):  
    c = {}
    c['cookie'] = iTV.getCookie()
    c['email'] = email
    c['password'] = password
    
    if c['cookie']:
      cache.set('cookie', urllib.urlencode(c))
    
  iTV.setCookie(c['cookie'])

def dropCookie():
  cache.delete('cookie')

def build_login_dir():
  
  listitem = xbmcgui.ListItem('[ Prisijungti ]')
  listitem.setProperty('IsPlayable', 'False')
  xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = sys.argv[0] + '?mode=5', listitem = listitem, isFolder = True, totalItems = 0)  
  
  xbmcplugin.setContent(int( sys.argv[1] ), 'tvshows')
  xbmc.executebuiltin('Container.SetViewMode(515)')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
def login():
  
  settings.openSettings()
  xbmc.executebuiltin('Container.Refresh')
  
# **************** main ****************

path = sys.argv[0]
params = getParameters(sys.argv[2])
mode = None
url = None

email = settings.getSetting('email')
password = settings.getSetting('password')

iTV = InternetoTV()
iTV.setCredential(email, password)

try:
  mode = int(params["mode"])
except:
  pass

try:
  url = urllib.unquote_plus(params["url"])
except:
  pass
     
if mode == None:
  if email and password:
    build_main_directory()
  else:
    build_login_dir()
elif mode == 1:
  play_channel(url)
elif mode == 2:
  build_archive_dir()
elif mode == 3:
  build_cat_dir(url)
elif mode == 4:
  play_video(url)
elif mode == 5:
  login()
  