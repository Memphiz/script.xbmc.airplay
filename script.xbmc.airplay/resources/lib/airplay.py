'''
    AirPlay for XBMC
    Copyright (C) 2012 Team XBMC

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import time
import threading
import BaseHTTPServerMod
import shutil
import xbmc
import xbmcgui
import urllib
from SocketServer import ThreadingMixIn

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__settings__   = sys.modules[ "__main__" ].__settings__
__cwd__        = sys.modules[ "__main__" ].__cwd__
__icon__       = sys.modules[ "__main__" ].__icon__
AIRPLAY_TEMP_IMAGE_PATH = sys.modules["__main__"].AIRPLAY_TEMP_IMAGE_PATH
sys.path.append (__cwd__)

import airplaystr
import digestauth
import biplist
from settings import *
from audiooutput import audiooutput_playback_running

AIRPLAY_STATUS_OK                  = 200
AIRPLAY_STATUS_SWITCHING_PROTOCOLS = 101
AIRPLAY_STATUS_NEED_AUTH           = 401
AIRPLAY_STATUS_NOT_FOUND           = 404
AIRPLAY_STATUS_METHOD_NOT_ALLOWED  = 405
AIRPLAY_STATUS_NOT_IMPLEMENTED     = 501
AIRPLAY_STATUS_NO_RESPONSE_NEEDED  = 1000   #custom!

#the delay after stopping which will
#lead to airplay_isPlaying return False
#this is needed for deal with some wonky
#airplay apps on ios5 (apple trailers app)
#which starts and stops a bunch off times
#before it settles
AIRPLAY_AIRTUNES_BLOCK_DELAY       = 3



EVENT_NONE    = -1
EVENT_PLAYING = 0
EVENT_PAUSED  = 1
EVENT_LOADING = 2
EVENT_STOPPED = 3
global g_eventStrings
g_eventStrings = ['playing', 'paused', 'loading', 'stopped']

global g_usePassword
global g_password
global g_airplayThread
global g_isPlaying
global g_isPlaybackReallyStarted
global g_reverseFiles
global g_lastEvent
global g_macAdr
global g_lastComTime

# global functions
def log(loglevel, msg):  
  xbmc.log("### [%s] - %s" % (__scriptname__,msg,),level=loglevel ) 

def timeToSecs(timeAr):
  arLen = len(timeAr)
  if arLen == 1:
    if len(timeAr[0]) > 0:
      currentSecs = int(timeAr[0])
    else:
      currentSecs = 0
  elif arLen == 2:
    currentSecs = int(timeAr[0]) * 60 + int(timeAr[1])
  elif arLen == 3:
    currentSecs = int(timeAr[0]) * 60 * 60 + int(timeAr[1]) * 60 + int(timeAr[2])
  return currentSecs

def getCurrentTimeSecs():
  currentTimeAr = xbmc.getInfoLabel("Player.Time").split(":")
  return timeToSecs(currentTimeAr)

def getCurrentDurationSecs():
  currentDurationAr = xbmc.getInfoLabel("Player.Duration").split(":")
  return timeToSecs(currentDurationAr)

class MultiThreadedHTTPServer(ThreadingMixIn, BaseHTTPServerMod.HTTPServer):
  pass

class AirPlayHandler(BaseHTTPServerMod.BaseHTTPRequestHandler):

  def do_GET(self):
    self.protocol_version = 'HTTP/1.1'
    self.handleAirplayProtocol("GET")

  def do_POST(self):
    self.protocol_version = 'HTTP/1.1'
    self.handleAirplayProtocol("POST")

  def do_PUT(self):
    self.protocol_version = 'HTTP/1.1'
    self.handleAirplayProtocol("PUT")
    
  def do_HTTP(self):
    pass #ignore the http event answers
  
  def handleAirplayProtocol(self, method):
    global g_usePassword
    global g_lastComTime
    
    self.uri              = self.path;    
    self.contentType      = self.headers.get('content-type')
    self.sessionId        = self.headers.get("x-apple-session-id")
    self.authorization    = self.headers.get("authorization")
    self.bodySize         = int(self.headers.get('Content-Length'))
    self.body             = ""
    self.needsAuth        = False
    self.method           = method
    self.uriParams        = ""
    handled               = True

    if self.bodySize:
      try:
        self.body        = self.rfile.read(self.bodySize)
      except:
        log(xbmc.LOGDEBUG, "can't read complete body (tried to read " + str(self.bodySize) + " bytes)")
        self.body = ""
    
    #password protect airplay via digest auth if needed
    if g_usePassword:
      #log(xbmc.LOGDEBUG,"Password log specified - request auth.")
      users = { airplaystr.AUTH_DIGEST_USERNAME : g_password}
      digestAuth = digestauth.DigestAuth(airplaystr.AUTH_DIGEST_REALM, users)
      if self.authorization == None:
        self.authorization = ''
      code, headers, body = digestAuth.authenticate(self.method, self.uri, self.authorization, True)#true for ignoreusername

      if code != AIRPLAY_STATUS_OK:
        self.sendGeneralResponse(code, False)#false for not finishing headers

      for key, value in headers:
        self.send_header(key,value)
     
      if code != AIRPLAY_STATUS_OK:
        #log(xbmc.LOGDEBUG,"Wrong password.Code: " + str(code))      
        self.end_headers()
        return

    #strip of params of uri
    self.startParamIdx = self.uri.find('?')
    if self.startParamIdx != -1:
      self.uriParams = self.uri[self.startParamIdx : len(self.uri)]
      self.uri = self.uri[0:self.startParamIdx]
    
    #distribute to handlers
    if self.uri == "/reverse":
      self.handleReverse()
    elif self.uri == "/rate":
      self.handleRate()
    elif self.uri == "/play":
      self.handlePlay()
    elif self.uri == "/scrub":
      self.handleScrub()
    elif self.uri == "/stop":
      self.handleStop()
    elif self.uri == "/photo":
      self.handlePhoto()
    elif self.uri == "/playback-info":
      self.handlePlaybackInfo()
    elif self.uri == "/server-info":
      self.handleServerInfo()
    elif self.uri == "/slideshow-features":
      self.handleSlideshowFeature()
    elif self.uri == "/authorize":
      self.handleAuthorize()
    elif self.uri == "/setProperty":
      self.handleSetProperty()
    elif self.uri == "/getProperty":
      self.handleGetProperty()
    elif self.uri == "/volume":
      self.handleVolume()
    else:
      handled = False
      self.send_response(AIRPLAY_STATUS_NOT_IMPLEMENTED)
      self.end_headers()
      
    if handled:
      log(xbmc.LOGDEBUG, "got request " + str(self.uri) + "(par: " + self.uriParams + ") with method: " + str(method))     
      if not audiooutput_playback_running():
        g_lastComTime = time.time()    
    else:
      log(xbmc.LOGERROR, "unhandled request " + str(self.uri)  + "(par: " + self.uriParams + ")\n")
  
  def handleReverse(self):
    global g_reverseFiles

    self.send_response(AIRPLAY_STATUS_SWITCHING_PROTOCOLS)
    self.send_header('Upgrade', 'PTTH/1.0\r\nConnection: Upgrade')
    self.send_header('Content-Length', 0)
    self.send_header('Connection', 'keep-alive')
    self.end_headers()

    #save reverse socket for session
    if self.sessionId != None and len(self.sessionId) > 0:
      g_reverseFiles[self.sessionId] = self.wfile
  
  def handleRate(self):
    foundIdx = self.uriParams.find("value=")
    rate = 0

    if foundIdx != -1:
      rate = int(float(self.uriParams[foundIdx + len("value=") : len(self.uriParams)]) + 0.5)

    if rate == 0:
      if xbmc.getCondVisibility("Player.Playing"):
        xbmc.executebuiltin('Action(pause)')
        self.sendReverseEvent(EVENT_PAUSED)
    else:
      if xbmc.getCondVisibility("Player.Paused"):
        xbmc.executebuiltin('Action(play)')
        self.sendReverseEvent(EVENT_PLAYING)
    self.sendGeneralResponse(AIRPLAY_STATUS_OK)

  def handlePlay(self):
    global g_lastEvent
    location = ""
    position = 0.0
    g_lastEvent = EVENT_NONE

    if self.contentType == "application/x-apple-binary-plist": 
      log(xbmc.LOGDEBUG, "parse binary plist")
      plist = biplist.readPlistFromString(self.body)

      if 'Start-Position' in plist:
        position = float(plist['Start-Position'])
      if 'Content-Location' in plist:
        location = plist['Content-Location']
    else:
      # Get URL to play
      startIdx = self.body.find("Content-Location: ")
      if startIdx == -1:
        self.sendGeneralResponse(AIRPLAY_STATUS_NOT_IMPLEMENTED)
        return 

      startIdx += len("Content-Location: ")
      endIdx = self.body.find('\n', startIdx)
      location = self.body[startIdx : endIdx]

      startIdx = self.body.find("Start-Position")
      if startIdx != -1:
        startIdx += len("Start-Position: ")
        endIdx = self.body.find('\n', startIdx)
        position = float(self.body[startIdx : endIdx])

    if len(location):
      #url encode useragent
      dict = { 'User-Agent' : 'AppleCoreMedia/1.0.0.8F455 (AppleTV; U; CPU OS 4_3 like Mac OS X; de_de)'}
      userAgent = urllib.urlencode(dict)
      location = location + "|" + userAgent
      log(xbmc.LOGDEBUG, "position: " + str(position))
      if position > 0.0:
        posPercent = position * 100
        listitem = xbmcgui.ListItem()      
        listitem.setProperty('StartPercent', str(posPercent))
        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(location, listitem)
      else:
        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(location)
      self.sendReverseEvent(EVENT_PLAYING)
    else:
      log(xbmc.LOGERROR, "no location found in play header")
    self.sendGeneralResponse(AIRPLAY_STATUS_OK)

  def handleScrub(self):
    if self.method == "GET":
      if getCurrentDurationSecs() > 0:
        position = getCurrentTimeSecs()
        respBody = "duration: %d\r\nposition: %f" % (getCurrentDurationSecs(), float(position))

        self.sendResponseWithBody(AIRPLAY_STATUS_OK, 'text/html', respBody)
      else:
        self.sendGeneralResponse(AIRPLAY_STATUS_METHOD_NOT_ALLOWED)
    else:#post method

      foundIdx = self.uriParams.find('position=')
      
      if foundIdx != -1:
        try:
          position = self.uriParams[foundIdx + len("position=") : len(self.uriParams)]
          duration = getCurrentDurationSecs()
          posPercent = float(float(position)*100 / getCurrentDurationSecs())
          xbmc.executebuiltin('playercontrol(seekpercentage(' + str(posPercent) + '))')
          log(xbmc.LOGDEBUG, "got POST request %s with pos %s" % (self.uri, str(position)))      
        except:
          log(xbmc.LOGDEBUG, "exception during position parsing - paras " + str(self.uriParams))
          pass
      self.sendGeneralResponse(AIRPLAY_STATUS_OK)

  def handleStop(self):
    global g_isPlaying
    global g_isPlaybackReallyStarted

    if g_isPlaying: #only stop player if we started him
      xbmc.executebuiltin('PlayerControl(Stop)')
      g_isPlaybackReallyStarted = False
    else: #if we are not playing and get the stop request - we just wanna stop picture streaming
      xbmc.executebuiltin('Action(previousmenu)')
    self.sendGeneralResponse(AIRPLAY_STATUS_OK, False)
    self.send_header('Connection', 'close')
    self.end_headers()
    self.sendReverseEvent(EVENT_STOPPED)
    if self.sessionId != None and len(self.sessionId) > 0:
      if g_reverseFiles[self.sessionId] != None:
        g_reverseFiles[self.sessionId].close()
        g_reverseFiles[self.sessionId] = None

  def handlePhoto(self):
    global g_lastEvent
    g_lastEvent = EVENT_NONE

    if self.bodySize > 0:
      tmpFile = open (AIRPLAY_TEMP_IMAGE_PATH, "wb") 
      try: 
        tmpFile.write(self.body)
#        shutil.copyfileobj (self.rfile, tmpFile) 
        #if writtenBytes > 0 and writtenBytes == self.bodySize: # evtl. fixme
        #g_application.getApplicationMessenger().PictureShow(tmpFilePath)    #fixme
        #else:
        #  log(xbmc.LOGERROR,"Error writing tmpFile.")
      except:
        log(xbmc.LOGERROR, "Error writing image to tmpfile.")
      finally: 
        tmpFile.close () 
        xbmc.executebuiltin('ShowPicture('+AIRPLAY_TEMP_IMAGE_PATH+')')
        
    self.sendGeneralResponse(AIRPLAY_STATUS_OK)

  def handlePlaybackInfo(self):
    global g_isPlaybackReallyStarted

    hasVideo = xbmc.getCondVisibility("Player.Playing") or xbmc.getCondVisibility("Player.Paused")
    position = 0.0
    duration = 0.0
    cacheDuration = 0.0
    playing = False
    
    if hasVideo:
      if not g_isPlaybackReallyStarted:
        #kill busydialog which might be opened by airtunes
        #because of ios5 client
        xbmc.executebuiltin("Dialog.Close(busydialog)")
      g_isPlaybackReallyStarted = True
      duration = getCurrentDurationSecs()
      if duration > 0:
        position = getCurrentTimeSecs()
        cacheDuration = float(duration * int(xbmc.getInfoLabel("Player.ProgressCache"))/float(100.0))
        playing = xbmc.getCondVisibility("Player.Playing")
      playingInt = 0
      
      if playing:
        playingInt = 1

#      log(xbmc.LOGDEBUG, "Info: dur: %d pos: %d cache: %f playing: %d" % (duration, position, cacheDuration, playingInt))
      
      respBody = airplaystr.PLAYBACK_INFO % (duration, cacheDuration, position, playingInt, duration)
      self.sendResponseWithBody(AIRPLAY_STATUS_OK, 'text/x-apple-plist+xml', respBody)
  
      if xbmc.getCondVisibility("Player.Caching"):
        self.sendReverseEvent(EVENT_LOADING)
      elif playing:
        self.sendReverseEvent(EVENT_PLAYING)
      else:
        self.sendReverseEvent(EVENT_PAUSED)
    else:#no video playing
      respBody = airplaystr.PLAYBACK_INFO_NOT_READY
      self.sendResponseWithBody(AIRPLAY_STATUS_OK, 'text/x-apple-plist+xml', respBody)      
      if g_isPlaybackReallyStarted and not airplay_isPlaying():
        self.sendReverseEvent(EVENT_STOPPED)
        g_isPlaybackReallyStarted = False

  def handleServerInfo(self):
    mac = settings_getMacAddress()
    respBody = airplaystr.SERVER_INFO % (mac)
    self.sendResponseWithBody(AIRPLAY_STATUS_OK, 'text/x-apple-plist+xml', respBody)
  
  def handleSlideshowFeature(self):
    self.sendGeneralResponse(AIRPLAY_STATUS_OK)
  
  def handleAuthorize(self):
    self.sendGeneralResponse(AIRPLAY_STATUS_OK)

  def handleSetProperty(self):
    self.sendGeneralResponse(AIRPLAY_STATUS_NOT_FOUND)

  def handleGetProperty(self):
    self.sendGeneralResponse(AIRPLAY_STATUS_NOT_FOUND)
  def handleVolume(self):
    foundIdx = self.uriParams.find('volume=')
      
    if foundIdx != -1:
      try:
        volume = float(self.uriParams[foundIdx + len("volume=") : len(self.uriParams)])
        volume = volume * 100
        xbmc.executebuiltin("SetVolume(%d,showvolumebar)" % volume)
      except:
        log(xbmc.LOGERROR,"Error parsing volume")
      finally:
        self.sendGeneralResponse(AIRPLAY_STATUS_OK)
  
  def sendResponseWithBody(self, status, contentType, body):
    self.send_response(status)
    self.send_header('Content-Type', contentType)
    self.send_header('Content-Length', len(body))
    self.send_header('Connection','keep-alive')
    self.end_headers()  
    self.wfile.write(body)
  
  def sendGeneralResponse(self, status, bFinishHeader = True):
    self.send_response(status)
    self.send_header('Content-Length', '0')
    self.send_header('Connection','keep-alive')
    if bFinishHeader:
      self.end_headers()

  def sendReverseEvent(self, state):
    global g_lastEvent
    global g_isPlaying
    
    if state == EVENT_STOPPED:
      g_isPlaying = False
    else:
      g_isPlaying = True
    
    if self.sessionId != None and len(self.sessionId) > 0:
      if self.sessionId in g_reverseFiles and g_reverseFiles[self.sessionId] != None:
        if g_lastEvent != state:
          body = ""
          header = ""
          if state >= 0 and state < len(g_eventStrings):        
            body = airplaystr.EVENT_INFO % g_eventStrings[state]
            log(xbmc.LOGDEBUG, "sending event: %s" % g_eventStrings[state])
          header = "POST /event HTTP/1.1\r\n"
          header += "Content-Type: text/x-apple-plist+xml\r\n"
          header += "Content-Length: " + str(len(body)) + "\r\n"
          header += "Connection: keep-alive\r\n"
          header += "x-apple-session-id: " + self.sessionId + "\r\n"
          header += "\r\n"
          if self.sessionId in g_reverseFiles:
            g_reverseFiles[self.sessionId].write(header)
            if len(body) > 0:
              g_reverseFiles[self.sessionId].write(body)
          else:
            log(xbmc.LOGERROR, "no reverse socket for sessionid.")
          g_lastEvent = state

class AirPlayServer (threading.Thread):
  def __init__(self, name):
      threading.Thread.__init__(self)
      self.name = name
      self.port = 36667
      self.abort = False

  def setPort(self, port):
    self.port = port
    
  def shutdown(self):
    global g_airplayThread
    self.abort = True
    self.httpd.shutdown()    
    log(xbmc.LOGDEBUG, "Waiting for server shutdown.")
    g_airplayThread.join()
    log(xbmc.LOGDEBUG, "Done waiting for server shutdown.")

  def run(self):
    log(xbmc.LOGDEBUG,"Thread started with port " + str(self.port))
    self.server_address = ('', self.port)
    server_class = MultiThreadedHTTPServer
    self.httpd = server_class(self.server_address, AirPlayHandler)
    self.httpd.protocol_version = 'HTTP/1.1'
    while not self.abort:
      try:
        self.httpd.serve_forever()
      except:
        log(xbmc.LOGDEBUG, "Exception on handle_request().")
    log(xbmc.LOGDEBUG,"Thread stopped")

    self.abort = False

def airplay_initGlobals():
  global g_usePassword
  global g_password
  global g_airplayThread
  global g_isPlaying
  global g_reverseFiles
  global g_lastEvent
  global g_isPlaybackReallyStarted
  global g_macAdr
  global g_lastComTime

  g_usePassword = False
  g_password = ""
  g_isPlaying = False
  g_airplayThread = None
  g_reverseFiles = dict()
  g_lastEvent = EVENT_NONE
  g_isPlaybackReallyStarted = False
  g_macAdr = ''
  g_lastComTime = time.time()

def airplay_setCredentials(usePassword, password):
  global g_usePassword
  global g_password
  g_usePassword = usePassword
  g_password = password

def airplay_startServer(port):
  global g_airplayThread
  airplay_stopServer()
  g_airplayThread = AirPlayServer("AirPlayServer") 

  log(xbmc.LOGDEBUG,"Starting server")
  g_airplayThread.setPort(port)
  g_airplayThread.daemon=True
  try:
    g_airplayThread.start()
  except:
    log(xbmc.LOGDEBUG, "thread was already running")

def airplay_serverRunning():
  global g_airplayThread
  if g_airplayThread != None:
    return g_airplayThread.isAlive()
  else:
    return False

def airplay_stopServer():
  global g_airplayThread
  if airplay_serverRunning():
    log(xbmc.LOGDEBUG,"Stopping server")
    g_airplayThread.shutdown()
    log(xbmc.LOGDEBUG,"Server stopped")
    
def airplay_isPlaying():
  global g_isPlaying
  return g_isPlaying

def airplay_blockAirtunes():
  if (time.time() - g_lastComTime) > AIRPLAY_AIRTUNES_BLOCK_DELAY:
    return False
  else:
    return True

def airplay_announceZeroconf(zeroconf, mac, friendlyName):
  global g_macAdr
  g_macAdr = mac
  zeroconf.addTxtRecord("deviceid", g_macAdr)
  zeroconf.addTxtRecord("features", airplaystr.AIRPLAY_ZEROCONF_RECORD_FEATURES)
  zeroconf.addTxtRecord("model",    airplaystr.AIRPLAY_ZEROCONF_RECORD_MODEL)
  zeroconf.addTxtRecord("srcvers",  airplaystr.AIRPLAY_ZEROCONF_RECORD_SRCVERS)
  return zeroconf.publishService(airplaystr.AIRPLAY_ZEROCONF_HANDLE, airplaystr.AIRPLAY_ZEROCONF_PROTO, friendlyName, settings_getAirplayServerPort())

def airplay_revokeZeroconf(zeroconf):
  zeroconf.removeService(airplaystr.AIRPLAY_ZEROCONF_HANDLE)
