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
import xbmc
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__settings__   = sys.modules[ "__main__" ].__settings__
__cwd__        = sys.modules[ "__main__" ].__cwd__
__icon__       = sys.modules[ "__main__" ].__icon__
sys.path.append (__cwd__)

#general
global g_airplayServerport
global g_airtunesServerport
global g_airtunesDebug
global g_passwordlock
global g_password
global g_zeroconfFriendlyName
global g_macAddress
global g_timer

#init globals with defaults
def settings_initGlobals():
  global g_airplayServerport
  global g_airtunesServerport
  global g_airtunesDebug
  global g_passwordlock
  global g_password
  global g_zeroconfFriendlyName
  global g_macAddress
  global g_timer
  
  g_airplayServerport     = 36667
  g_airtunesServerport    = g_airplayServerport + 1
  g_airtunesDebug         = False
  g_passwordlock          = False
  g_password	            = ""
  g_zeroconfFriendlyName  = xbmc.getInfoLabel("System.FriendlyName")
  g_macAddress            = xbmc.getInfoLabel("Network.MacAddress")
  if not ":" in g_macAddress:
    time.sleep(2)
    g_macAddress            = xbmc.getInfoLabel("Network.MacAddress")
  g_timer = time.time()
   
def settings_getAirplayServerPort():
  global g_airplayServerport
  return g_airplayServerport 

def settings_getAirtunesServerPort():
  global g_airtunesServerport
  return g_airtunesServerport 

def settings_getAirtunesDebug():
  global g_airtunesDebug
  return g_airtunesDebug

def settings_getPasswordLock():
	global g_passwordlock
	return g_passwordlock
	
def settings_getPassword():
	global g_password
	return g_password
  
def settings_getFriendlyName():
  global g_zeroconfFriendlyName
  return g_zeroconfFriendlyName
  
def settings_getMacAddress():
  global g_macAddress
  return g_macAddress

#check for new settings and handle them if anything changed
#only checks if the last check is 5 secs old
#returns true if settings have changed
def settings_checkForNewSettings():
#todo  for now impl. stat on addon.getAddonInfo('profile')/settings.xml and use mtime
#check for new settings every 5 secs
  global g_timer
  ret = False

  if time.time() - g_timer > 5:
    ret = settings_setup()
    g_timer = time.time()
  return ret
  
def settings_handleAirplaySettings():
  global g_airplayServerport
  global g_airtunesServerport
  global g_airtunesDebug
  global g_passwordlock
  global g_password
  global g_zeroconfFriendlyName
  settingsChanged = False
  
  airplayServerport = int(float(__settings__.getSetting("airplayport")))
  airtunesServerport = airplayServerport + 1
  airtunesDebug = __settings__.getSetting("airtunesdebug") == "true"
  passwordlock = __settings__.getSetting("airplaylock") == "true"
  password = __settings__.getSetting("airplaypassword")
  zeroconfFriendlyName  = xbmc.getInfoLabel("System.FriendlyName")

  if g_airplayServerport != airplayServerport:
    g_airplayServerport = airplayServerport
    settingsChanged = True

  if g_airtunesServerport != airtunesServerport:
    g_airtunesServerport = airtunesServerport
    settingsChanged = True

  if g_airtunesDebug != airtunesDebug:
    g_airtunesDebug = airtunesDebug
    settingsChanged = True

  if g_passwordlock != passwordlock:
    g_passwordlock = passwordlock
    settingsChanged = True

  if g_password != password:
    g_password = password
    settingsChanged = True
    
  if g_zeroconfFriendlyName != zeroconfFriendlyName:
    g_zeroconfFriendlyName = zeroconfFriendlyName
    settingsChanged = True

  return settingsChanged

#handles all settings of airplay and applies them as needed
#returns if a settings have changed
def settings_setup():  
  settingsChanged = False
  settingsChanged = settings_handleAirplaySettings()

  return settingsChanged
  
