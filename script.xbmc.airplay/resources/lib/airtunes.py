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
import xbmc

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__settings__   = sys.modules[ "__main__" ].__settings__
__cwd__        = sys.modules[ "__main__" ].__cwd__
__icon__       = sys.modules[ "__main__" ].__icon__
sys.path.append (__cwd__)

import digestauth
from settings import *
from shairport import *

global g_usePassword
global g_password
global g_airtunesThread
global g_macAdr

# global functions
def log(loglevel, msg):  
  xbmc.log("### [%s] - %s" % ('AirTunes',msg,),level=loglevel )
  
class AirTunesServer (threading.Thread):
  def __init__(self, name):
      threading.Thread.__init__(self)
      self.name = name
      self.abort = False
      self.port = 36668
      self.abort = False

  def setPort(self, port):
    self.port = port
    
  def shutdown(self):
    self.abort = True

    shairport_exit()    
    while airtunes_serverRunning():
      time.sleep(1)  
      log(xbmc.LOGDEBUG, "Waiting for server shutdown.")

  def initShairport(self):
    global g_macAdr
    global g_password 

    password = g_password
    if password == None:
      password = ''
    return shairport_init(g_macAdr,password,self.port)

  def run(self):
    if self.initShairport() == 0:
      log(xbmc.LOGERROR,"Error initialising libshairport")
      return
  
    log(xbmc.LOGDEBUG,"Thread started with port " + str(self.port))
    while not self.abort and shairport_is_running():
      try:
        log(xbmc.LOGDEBUG,"shairport_loop")
        shairport_loop()
      except:
        log(xbmc.LOGDEBUG, "Exception on shairport_loop().")
    log(xbmc.LOGDEBUG,"Thread stopped")
    self.abort = False

def airtunes_initGlobals():
  global g_usePassword
  global g_password
  global g_airtunesThread
  global g_macAdr
  g_usePassword = False
  g_password = ""
  g_airtunesThread = None
  g_macAdr = ""

def airtunes_setCredentials(usePassword, password):
  global g_usePassword
  global g_password
  g_usePassword = usePassword
  g_password = password
 
def airtunes_startServer(port):
  global g_airtunesThread
  global g_macAdr
  g_macAdr = airtunes_getStrippedMac(settings_getMacAddress())

  airtunes_stopServer()
  g_airtunesThread = AirTunesServer("AirTunesServer") 

  log(xbmc.LOGDEBUG,"Starting server")
  g_airtunesThread.setPort(port)
  try:
    g_airtunesThread.start()
  except:
    log(xbmc.LOGDEBUG, "thread was already running")

def airtunes_serverRunning():
  global g_airtunesThread
  if g_airtunesThread != None:
    return g_airtunesThread.isAlive()
  else:
    return False

def airtunes_stopServer():
  global g_airtunesThread
  if airtunes_serverRunning():
    log(xbmc.LOGDEBUG,"Stopping server")
    g_airtunesThread.shutdown()
    log(xbmc.LOGDEBUG,"Server stopped")

def airtunes_getStrippedMac(macAdr):
  strippedMac = macAdr.replace(":","")
  while len(strippedMac) < 12:
    strippedMac = "0" + strippedMac
  return strippedMac

def airtunes_announceZeroconf(zeroconf, mac, friendlyName):
  global g_macAdr
  airtunesMac = airtunes_getStrippedMac(mac)
  appName = "%s@%s" % (airtunesMac, friendlyName)
  
  zeroconf.addTxtRecord("cn", airplaystr.AIRTUNES_ZEROCONF_RECORD_CN)
  zeroconf.addTxtRecord("ch", airplaystr.AIRTUNES_ZEROCONF_RECORD_CH)
  zeroconf.addTxtRecord("ek", airplaystr.AIRTUNES_ZEROCONF_RECORD_EK)
  zeroconf.addTxtRecord("et", airplaystr.AIRTUNES_ZEROCONF_RECORD_ET)
  zeroconf.addTxtRecord("sv", airplaystr.AIRTUNES_ZEROCONF_RECORD_SV)
  zeroconf.addTxtRecord("tp", airplaystr.AIRTUNES_ZEROCONF_RECORD_TP)
  zeroconf.addTxtRecord("sm", airplaystr.AIRTUNES_ZEROCONF_RECORD_SM)
  zeroconf.addTxtRecord("ss", airplaystr.AIRTUNES_ZEROCONF_RECORD_SS)
  zeroconf.addTxtRecord("sr", airplaystr.AIRTUNES_ZEROCONF_RECORD_SR)
  zeroconf.addTxtRecord("pw", airplaystr.AIRTUNES_ZEROCONF_RECORD_PW)
  zeroconf.addTxtRecord("vn", airplaystr.AIRTUNES_ZEROCONF_RECORD_VN)
  zeroconf.addTxtRecord("txtvers", airplaystr.AIRTUNES_ZEROCONF_RECORD_TXTVERS)
  return zeroconf.publishService(airplaystr.AIRTUNES_ZEROCONF_HANDLE, airplaystr.AIRTUNES_ZEROCONF_PROTO, appName, settings_getAirtunesServerPort())

def airtunes_revokeZeroconf(zeroconf):
  zeroconf.removeService(airplaystr.AIRTUNES_ZEROCONF_HANDLE)