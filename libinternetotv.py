# -*- coding: utf-8 -*-

import re
import urllib
import urllib2
import sys

from StringIO import StringIO
import gzip

from bs4 import BeautifulSoup

reload(sys) 
sys.setdefaultencoding('utf8')

import httplib

class InternetoTV(object):
  
  def __init__(self):
    self.USERNAME = ''
    self.PASSWORD = ''
    self.COOKIE = None
    self.HOST = 'www.interneto.tv'
    self.HTTP = None
    self.HTTPS = None

  def getHTTP(self):
    if not self.HTTP:      
      self.HTTP = httplib.HTTPConnection(self.HOST)
    return self.HTTP
  
  def getHTTPS(self):
    if not self.HTTPS:      
      self.HTTPS = httplib.HTTPSConnection(self.HOST)
    return self.HTTPS

  def setCredential(self, username, password):
    self.USERNAME = username
    self.PASSWORD = password
  
  def unzipResponse(self, response):
    
    if response.getheader('Content-Encoding') == 'gzip':
      buf = StringIO(response.read())
      f = gzip.GzipFile(fileobj=buf)
      return f.read()
    else:    
      return response.read()

  def getCookie(self):

    loginData = {}
    loginData['data[AppUser][email]'] = self.USERNAME
    loginData['data[AppUser][password]'] = self.PASSWORD
    loginData['data[AppUser][remember]'] = '1'
    loginData = urllib.urlencode(loginData)

    c = self.getHTTPS()
    c.request("POST", "/prisijungti", loginData, {'Content-type': 'application/x-www-form-urlencoded', 'Accept-encoding': 'gzip'})
    response = c.getresponse()
    fdata = self.unzipResponse(response)

    cookie = response.getheader('set-cookie') 

    ITVAPP = ''
    ITVCOOKIE = ''

    for c in cookie.replace(',',';').split(';'):
      p = c.split('=')
      
      key = p[0].strip()
      if key == 'ITVAPP':
	ITVAPP = p[1].strip()
      if key == 'ITVCOOKIE[remember_me]':
	ITVCOOKIE = p[1].strip()
      
    if ITVAPP and ITVCOOKIE:
      self.COOKIE = 'ITVAPP=%s; ITVCOOKIE[remember_me]=%s' % (ITVAPP, ITVCOOKIE)
      return self.COOKIE
	
    else:
      return None
    
  def setCookie(self, cookie):    
    self.COOKIE = cookie
    
  def n18(self):
    c = self.getHTTP()
    c.request("GET", "/n18/1", headers = {'Cookie': self.COOKIE, 'Accept-encoding': 'gzip'})
    c.getresponse().read()
      
  def getChannelUrls(self, vid):
    
    videoData = {}

    c = self.getHTTP()
    c.request("GET", "/kanalas/" + vid, headers = {'Cookie': self.COOKIE, 'Accept-encoding': 'gzip'})
    response = c.getresponse()
    fdata = self.unzipResponse(response)
    
    if response.getheader('location') and response.getheader('location').startswith('http://www.interneto.tv/n18'):
      self.n18()
      c.request("GET", "/kanalas/" + vid, headers = {'Cookie': self.COOKIE, 'Accept-encoding': 'gzip'})
      fdata = self.unzipResponse(c.getresponse())
      
    soup = BeautifulSoup(fdata, 'html.parser')
    
    ico_logout = soup.find('a', class_='ico-logout')
    if not ico_logout:
      return { 'login_failed' : True }

    player_wrapper = soup.find('div', class_='player-wrapper')
    
    if not player_wrapper:      
      content = soup.find('div', id='content')
      return { 'error' : content.h1.text }

    links = player_wrapper.find_all('a')

    videoData['RTMP'] = links[1]['href'] #RTMP

    epg_first = soup.find('div', id='epg-first')

    img = epg_first.find('img')

    videoData['img'] = img['src'] #IMG

    videoData['title'] = epg_first.find('div', class_='title').string

    videoData['description'] = epg_first.find('div', class_='description').string

    videoData['mp4_hls'] = re.findall(' \[\{type\: \'hls\', file\: \'([^\']*)\'', fdata, re.DOTALL)[0]

    return videoData

  def getChannels(self):
    
    result = []
    
    c = self.getHTTP()
    c.request("GET", "/kanalai", headers = {'Accept-encoding': 'gzip'})
    fdata = self.unzipResponse(c.getresponse())
    
    soup = BeautifulSoup(fdata, 'html.parser')
    
    ul = soup.find('ul', class_='channels-list')
    
    for channel in ul.find_all('a'):
      
      ch = {}
      ch['id'] = channel['href'].split('/')[2] 
      ch['icon'] = channel.span.img['src']
      ch['title'] = channel.span.img['alt']
      
      result.append(ch)
      
    return result

  def getVideoCats(self):
    
    cats = []
    
    c = self.getHTTP()
    c.request("GET", "/tvirasai", headers = {'Accept-encoding': 'gzip'})
    fdata = self.unzipResponse(c.getresponse())
    
    soup = BeautifulSoup(fdata, 'html.parser')    
    
    wrappers = soup.find_all('div', class_='carousel-wrapper')
    for wrapper in wrappers: 
      
      cat = {}
      
      cat['id'] = wrapper.find('div', class_='iosslider')['id']      
      cat['title'] = wrapper.previous_sibling.previous_sibling.span.text
      
      cats.append(cat)
    
    return cats
  
  def getVideoCat(self, cid):
    
    videos = []
    
    c = self.getHTTP()
    c.request("GET", "/tvirasai", headers = {'Accept-encoding': 'gzip'})
    fdata = self.unzipResponse(c.getresponse())
    
    soup = BeautifulSoup(fdata, 'html.parser')
    
    cat = soup.find('div', id=cid)
    
    vids = cat.find_all('div', class_='slide')
    for vid in vids:
      
      video = {}
      
      video['image'] = vid.img['src']
      video['url'] = vid.a['href']
      video['title'] = vid.find('span', class_='title').text
      video['date'] = vid.find('span', class_='time-day').text
      
      videos.append(video)
      
    return videos
  
  def getVideoURL(self, url):
    
    videoData = {}
    
    c = self.getHTTP()
    c.request("GET", url, headers = {'Cookie': self.COOKIE, 'Accept-encoding': 'gzip'})
    response = c.getresponse()
    fdata = self.unzipResponse(response)
    
    if response.getheader('location') and response.getheader('location').startswith('http://www.interneto.tv/n18'):
      self.n18()
      c.request("GET", url, headers = {'Cookie': self.COOKIE, 'Accept-encoding': 'gzip'})
      fdata = self.unzipResponse(c.getresponse())
    
    soup = BeautifulSoup(fdata, 'html.parser')
    
    ico_logout = soup.find('a', class_='ico-logout')
    if not ico_logout:
      return { 'login_failed' : True }
    
    player_wrapper = soup.find('div', class_='player-wrapper')

    links = player_wrapper.find_all('a')

    videoData['mp4_hls'] = links[1]['href']
    
    if not videoData['mp4_hls'].startswith('http'):
      videoData['mp4_hls'] = re.findall('\[\{sources\: \[\{file\: "([^"]*)"', fdata, re.DOTALL)[0]

    epg_first = soup.find('div', id='epg-first')

    img = epg_first.find('img')

    videoData['img'] = img['src'] #IMG

    videoData['title'] = epg_first.find('div', class_='title').string
    
    return videoData
