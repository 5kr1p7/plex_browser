#!/usr/bin/python3

import sys
import requests
import xmltodict
from bs4 import BeautifulSoup
import logging
from pprint import pprint

# --------------------------------
#logging.basicConfig(level = logging.DEBUG)
#logging.StreamHandler(sys.stdout)
# --------------------------------

if len(sys.argv) < 2:
  print('Usage: ' + sys.argv[0] + ' <IP>')
  sys.exit(2)
else:
  if len(sys.argv) == 3:
    section = sys.argv[2]

url = sys.argv[1]
types = ['movie', 'show']


class Plex():
  '''
  Get info from Plex device.
  
  Args:
    host(str): Device's hostname or IP address
    port(int): Port (default is 32400)
  '''
  def __init__(self, host: str, port: int = 32400):
    self.host = host
    self.url = f"{host}:{port}"
    self.token = self.getToken()
    self.sections = self.getSections()

    
  def getToken(self) -> str:
    '''Get token from settings page.'''
    settings_page = requests.get(f"http://{self.host}:8181/settings")
    settings_soup = BeautifulSoup(settings_page.text, 'html.parser')
    token_tag =  settings_soup.find('input', {'id': 'pms_token'})
    
    return token_tag['value']


  def genUrl(self, path: str) -> str:
    '''Generate URL with token.'''
    return f"http://{self.url}{path}?X-Plex-Token={self.token}"


  def getVideoLink(self, data) -> str:
    '''Generate link to video file.'''
    if type(data) is not list:
      if not type(data['Part']) is list:
        return self.genUrl(data['Part']['@key'])
    return ''

  
  def getSections(self) -> dict:
    '''Get sections (libraries) from device.'''
    sections_url = self.genUrl('/library/sections/')
    response = requests.get(sections_url)
    if response.status_code != requests.codes.ok:
      print('Bad status code of request!')
      exit(1)
    sections = xmltodict.parse(response.content)['MediaContainer']['Directory']
    
    sections_list = {}
    for directory in sections:
        if directory['@type'] in types:
            sections_list[directory['@key']] = {
                'key': directory['@key'],
                'type': directory['@type'],
                'title': directory['@title']
            }
    return sections_list

  
  def getVideosFromSection(self, section_id: int) -> dict:
    '''Get videos list from section(library).'''
    videos_url = self.genUrl('/library/sections/' + str(section_id) + '/all')
    response = requests.get(videos_url)
    videos = xmltodict.parse(response.content)

    if not videos['MediaContainer'].get('Video'):
        return []
  
    title = videos['MediaContainer']['@title1'] + ' / ' + videos['MediaContainer']['@title2']
    videos_list = []

    for video in videos['MediaContainer']['Video']:
      title = video.get('@title') or 'NO TITLE'
      videos_list.append({ '_title': title, 'link': self.getVideoLink(video['Media']) })
    
    return videos_list


plexDevice = Plex(url)

if len(sys.argv) < 3:
  pprint(plexDevice.sections)

try:
  pprint(plexDevice.getVideosFromSection(section))
except NameError:
  pass
