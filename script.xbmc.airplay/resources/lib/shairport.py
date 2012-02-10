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

'''

cheat sheet


c_int(g_libshairport.shairport_main(int argc, char **argv))
g_libshairport.shairport_exit(void)
c_int(g_libshairport.shairport_loop(void))
c_int(g_libshairport.shairport_is_running(void))
g_libshairport.shairport_set_ao(struct AudioOutput *ao)
g_libshairport.shairport_set_printf(struct printfPtr *funcPtr)

'''
import platform
import xbmc
import sys
import os

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__settings__ = sys.modules[ "__main__" ].__settings__
__cwd__ = sys.modules[ "__main__" ].__cwd__

__libbaseurl__ = sys.modules[ "__main__" ].__libbaseurl__
__libnameosx__ = sys.modules[ "__main__" ].__libnameosx__
__libnameios__ = sys.modules[ "__main__" ].__libnameios__
#__libnamewin__ = sys.modules[ "__main__" ].__libnamewin__

global g_shairportLoaded
global g_libshairport
global g_printfCallback
global g_ao
g_printfCallback = None
g_ao = None

try:
  from ctypes import *
  HAVE_CTYPES = True
except:
  HAVE_CTYPES = False

if HAVE_CTYPES:
  from audiooutput import *
  
def log(loglevel, msg):  
  xbmc.log("### [%s] - %s" % ('ShairPort',msg,),level=loglevel ) 
  
  
'''
struct printfPtr
{
  int (*extprintf)(const char* msg, size_t msgSize);
};
'''

extprintf_prototype = CFUNCTYPE(c_int, c_char_p, c_size_t)
#extprintf_prototype = WINFUNCTYPE(c_int, c_char_p, c_size_t) #windows


class printfPtr(Structure):
  _fields_ = [("extprintf",  extprintf_prototype)]

def shairport_loadLibshairport():
  global g_shairportLoaded
  global g_libshairport  
  ret = 0

  if HAVE_CTYPES:
    libname = "libshairport.so" #default to linux type
    # load libshairport.so/dylib
    try:
      if xbmc.getCondVisibility('system.platform.osx'):
        libname = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib', __libnameosx__) )
        if not os.path.exists(libname):
          ret = 1
        else:
          cdll.LoadLibrary(libname)
          g_libshairport = CDLL(libname)
      elif  xbmc.getCondVisibility('system.platform.ios'):
        libname = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib', __libnameios__) )
        if not os.path.exists(libname):
          ret = 1
        else:
          cdll.LoadLibrary(libname)
          g_libshairport = CDLL(libname)
#      elif xbmc.getCondVisibility('system.platform.windows'): 
#         libname = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib', __libnamewin__) )
#        if not os.path.exists(libname):
#          ret = 1
#        else:
#          cdll.LoadLibrary(libname)
#          g_libshairport = CDLL(libname)
      else:
        cdll.LoadLibrary("libshairport.so")
        g_libshairport = CDLL("libshairport.so")

      g_libshairport.shairport_main.restype=c_int
      g_libshairport.shairport_main.argtypes = [c_int, POINTER(c_char_p)]
      g_libshairport.shairport_loop.restype=c_int
      g_libshairport.shairport_is_running.restype=c_int
      g_libshairport.shairport_set_ao.argtypes = [POINTER(AudioOutput)]
      g_libshairport.shairport_set_printf.argtypes = [POINTER(printfPtr)]
    except:
      g_shairportLoaded = False
      log(xbmc.LOGERROR, "shairport: Error loading " + libname)
      ret = 1
  else:
    log(xbmc.LOGERROR, "shairport: No ctypes available.")
    ret = 2
    g_shairportLoaded = False
  return ret
 
def shairport_init(macAdr, password, port):
  shairport_set_ao()
  shairport_set_printf()
  return shairport_main(macAdr, password, port)

 
def shairport_main(macAdr, password, port):
  numArgs = 4;
  hwStr = "--mac=%s" % macAdr
  pwStr = "--password=%s" % password
  portStr = "--server_port=%s" % str(port)
  if len(password) > 0:
    numArgs += 1
  
  CSTR_ARRAY = c_char_p * 6
  argv = CSTR_ARRAY("self","--apname=XBMC", portStr, hwStr, pwStr, None) # the 1st argv is the program name

  return c_int(g_libshairport.shairport_main(numArgs, argv))

def shairport_exit():
  g_libshairport.shairport_exit()

def shairport_loop():
  return c_int(g_libshairport.shairport_loop())

def shairport_is_running():
  return c_int(g_libshairport.shairport_is_running()) != 0


def shairport_log(msg, size):  
  if settings_getAirtunesDebug():
    log(xbmc.LOGDEBUG, "%s" % msg)
  return 1
  
def shairport_set_ao():
  global g_ao
  g_ao = AudioOutput()
  g_ao.ao_initialize = ao_initialize_prototype(audiooutput_initialize)
  g_ao.ao_play = ao_play_prototype(audiooutput_play)
  g_ao.ao_default_driver_id = ao_default_driver_id_prototype(audiooutput_default_driver_id)
  g_ao.ao_open_live = ao_open_live_prototype(audiooutput_open_live)
  g_ao.ao_close = ao_close_prototype(audiooutput_close)
  g_ao.ao_append_option = ao_append_option_prototype(audiooutput_append_option)
  g_ao.ao_free_options = ao_free_options_prototype(audiooutput_free_options)
  g_ao.ao_get_option = ao_get_option_prototype(audiooutput_get_option)
  log(xbmc.LOGDEBUG, "setting up AudioOutput")
  g_libshairport.shairport_set_ao(pointer(g_ao))

def shairport_set_printf():
  global g_printfCallback
  g_printfCallback = printfPtr(extprintf_prototype(shairport_log))
  g_libshairport.shairport_set_printf(pointer(g_printfCallback))


