'''
    AirPlay for XBMC
    Copyright (C) 2011 Team XBMC

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


import xbmc
import xbmcaddon
import xbmcgui
import time
import os

__settings__   = xbmcaddon.Addon(id='script.xbmc.airplay')
__cwd__        = __settings__.getAddonInfo('path')
__icon__       = os.path.join(__cwd__,"icon.png")
__scriptname__ = "XBMC AirPlayServer"

__libbaseurl__ = "http://mirrors.xbmc.org/build-deps/addon-deps/binaries/libshairport"
__libnameosx__ = "libshairport-osx.0.dylib"
__libnameios__ = "libshairport-ios.0.dylib"
#__libnamewin__ = "libshairport-win32.0.dll"

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
AIRPLAY_TEMP_IMAGE_PATH = xbmc.translatePath(os.path.join('special://temp','airplay_photo.jpg'))
sys.path.append (BASE_RESOURCE_PATH)

'''
xbmc.log("Started")

while 1:
    print "Abort Requested: "+str(xbmc.abortRequested)
    if (xbmc.abortRequested):
        xbmc.log("Aborting...")
        break
    time.sleep(1)

xbmc.log("Exiting")
'''
from settings import *
from airplay import *
from airtunes import *
from shairport import shairport_loadLibshairport
from tools import tools_downloadLibShairport

global g_zeroconf
global g_airtunesAvailable

# global functions
def log(loglevel, msg):  
  xbmc.log("### [%s] - %s" % (__scriptname__,msg,),level=loglevel ) 
  
def initGlobals():
  global g_zeroconf
  global g_airtunesAvailable
  
  g_zeroconf = xbmc.Zeroconf()
  g_airtunesAvailable = False
  settings_initGlobals()
  airplay_initGlobals()
  airtunes_initGlobals()

def initServers():
  global g_airtunesAvailable

  airplay_setCredentials(settings_getPasswordLock(),settings_getPassword())
  airplay_startServer(settings_getAirplayServerPort())
  if g_airtunesAvailable:
    airtunes_setCredentials(settings_getPasswordLock(),settings_getPassword())
    airtunes_startServer(settings_getAirtunesServerPort())
  announceZeroconfService()
  
def deinitServers():
  global g_airtunesAvailable

  airplay_stopServer()
  if g_airtunesAvailable:
    airtunes_stopServer()
  deAnnounceZeroconfService()


def process_airplay():
  global g_airtunesAvailable
  while not xbmc.abortRequested:

    initServers()
    
    while not xbmc.abortRequested:
      time.sleep(1)
      
      #on settings change -> around the world
      if settings_checkForNewSettings():
        break
      #on server breakdown -> around the world
      if not airplay_serverRunning() or ( g_airtunesAvailable and not airtunes_serverRunning() ):
        log(xbmc.LOGERROR, "Unexpected server shutdown")
        break
  
    deinitServers()
    
def announceZeroconfService():
  global g_zeroconf
  
  macAdr = settings_getMacAddress()
  friendlyName = settings_getFriendlyName()

  #announce airplay
  ret = airplay_announceZeroconf(g_zeroconf, macAdr, friendlyName)
  if not ret:
    log(xbmc.LOGERROR, "Error announcing airplay zeroconf service")
  
  #announce airtunes
  if g_airtunesAvailable:
    ret = airtunes_announceZeroconf(g_zeroconf, macAdr, friendlyName)
    if not ret:
      log(xbmc.LOGERROR, "Error announcing airtunes zeroconf service")

  return ret

def deAnnounceZeroconfService():
  global g_zeroconf
  airplay_revokeZeroconf(g_zeroconf)
  if g_airtunesAvailable:
    airtunes_revokeZeroconf(g_zeroconf)

#MAIN - entry point
initGlobals()
g_airtunesAvailable = False
loaded = -1

#no shairport for windows yet
if not xbmc.getCondVisibility('system.platform.windows'):
  loaded = shairport_loadLibshairport()

if loaded == 1:			#libshairport not found
#ask user if we should fetch the lib for osx (later ios and windows
  if xbmc.getCondVisibility('system.platform.osx'): #or xbmc.getCondVisibility('system.platform.windows'):
    t1 = __settings__.getLocalizedString(504)
    t2 = __settings__.getLocalizedString(509)
    if xbmcgui.Dialog().yesno(__scriptname__,t1,t2):
      tools_downloadLibShairport()
      loaded = shairport_loadLibshairport()

  if xbmc.getCondVisibility('system.platform.linux'):
    t1 = __settings__.getLocalizedString(504)
    t2 = __settings__.getLocalizedString(505)
    t3 = __settings__.getLocalizedString(506)
    xbmcgui.Dialog().ok(__scriptname__,t1,t2,t3)
elif loaded == 2:		#no ctypes available
  t1 = __settings__.getLocalizedString(507)
  t2 = __settings__.getLocalizedString(508)
  xbmcgui.Dialog().ok(__scriptname__,t1,t2) 

if loaded == 0:
  g_airtunesAvailable = True
else:
  log(xbmc.LOGERROR, "Libshairport not available or not support - disable airtunes support.")
#main loop
settings_setup()
process_airplay()    #airplay loop
log(xbmc.LOGDEBUG,"AirPlay script cleaned up")
