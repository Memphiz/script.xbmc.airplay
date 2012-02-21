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
import xbmcgui
import struct

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__settings__   = sys.modules[ "__main__" ].__settings__
__cwd__        = sys.modules[ "__main__" ].__cwd__
__icon__       = sys.modules[ "__main__" ].__icon__
sys.path.append (__cwd__)

from ctypes import *
from airplay import *
AO_PIPE_NAME = 'pipe://airtunes_ao/stream'
BXA_PACKET_TYPE_FMT  = 1

global g_pipesManager
global g_options
g_pipesManager = xbmc.PipesManager()
g_options = dict()

'''
typedef struct{  
char fourcc[4];  
uint32_t type;  
uint32_t channels;  
uint32_t sampleRate;  
uint32_t bitsPerSample;  
uint64_t durationMs;
}__attribute__((__packed__)) BXA_FmtHeader;
'''

class BXA_FmtHeader(Structure):
  _fields_ = [("fourcc",        c_char*4),
              ("type",          c_uint32),
              ("channels",      c_uint32),
              ("sampleRate",    c_uint32),
              ("bitsPerSample", c_uint32),
              ("durationMs",    c_uint64)]

'''
struct ao_device_xbmc
{
  XFILE::CFilePipe *pipe;
};
'''
#only pass the opaque pointer - this even could be removed from libshairport because its unused
class ao_device_xbmc(Structure):
  pass 
  
'''
typedef struct ao_sample_format {
  int  bits; /* bits per sample */
  int  rate; /* samples per second (in a single channel) */
  int  channels; /* number of audio channels */
  int  byte_format; /* Byte ordering in sample, see constants below */
        char *matrix; /* input channel location/ordering */
} ao_sample_format;
'''
class ao_sample_format(Structure):
  _fields_ = [("bits",        c_int),
              ("rate",        c_int),
              ("channels",     c_int),
              ("byte_format", c_int),
              ("matrix",      c_char_p)]

'''
typedef struct ao_option {
  char *key;
  char *value;
  struct ao_option *next;
} ao_option;
'''
class ao_option(Structure):
  pass

#ao interface function prototypes
ao_initialize_prototype = CFUNCTYPE(None) # void ao_initialize(void);
#use c_void_p as argument instead of c_char_p - else we are treated as string and not as buffer
ao_play_prototype = CFUNCTYPE(c_int,  POINTER(ao_device_xbmc), c_void_p, c_uint32) #int ao_play(ao_device *, char *, uint32_t);  
ao_default_driver_id_prototype = CFUNCTYPE(c_int);#int (*ao_default_driver_id)(void);
#ao_open_live_prototype = CFUNCTYPE(POINTER(ao_device_xbmc), c_int, POINTER(ao_sample_format), POINTER(ao_option))#ao_device* (*ao_open_live)( int, ao_sample_format *, ao_option *);
ao_open_live_prototype = CFUNCTYPE(c_void_p, c_int, POINTER(ao_sample_format), POINTER(ao_option))#ao_device* (*ao_open_live)( int, ao_sample_format *, ao_option *);
ao_close_prototype = CFUNCTYPE(c_int, POINTER(ao_device_xbmc))#int (*ao_close)(ao_device *);     
ao_append_option_prototype = CFUNCTYPE(c_int, POINTER(POINTER(ao_option)), c_char_p, c_char_p)#int (*ao_append_option)(ao_option **, const char *, const char *);
ao_free_options_prototype = CFUNCTYPE(None, POINTER(ao_option))#void (*ao_free_options)(ao_option *);
ao_get_option_prototype = CFUNCTYPE(c_void_p, c_char_p)#char* (*ao_get_option)(ao_option *, const char* );

'''
struct AudioOutput                                                                                                                                                                                              
{                                                                                                                                                                                                              
      void (*ao_initialize)(void);                                                                                                                                                                               
      int (*ao_play)(ao_device *, char *, uint32_t);                                                                                                                                                             
      int (*ao_default_driver_id)(void);                                                                                                                                                                         
      ao_device* (*ao_open_live)( int, ao_sample_format *, ao_option *);
      int (*ao_close)(ao_device *);                                                                                                                                                                              
      /* -- Device Setup/Playback/Teardown -- */                                                                                                                                                                 
      int (*ao_append_option)(ao_option **, const char *, const char *);                                                                                                                                         
      void (*ao_free_options)(ao_option *);                                                                                                                                                                      
      char* (*ao_get_option)(ao_option *, const char* );                                                                                                                                                         
}; 
'''
class AudioOutput(Structure):     
  _fields_ = [('ao_initialize',         ao_initialize_prototype),
              ('ao_play',               ao_play_prototype),
              ('ao_default_driver_id',  ao_default_driver_id_prototype),
              ('ao_open_live',          ao_open_live_prototype),
              ('ao_close',              ao_close_prototype),
              ('ao_append_option',      ao_append_option_prototype),
              ('ao_free_options',       ao_free_options_prototype),
              ('ao_get_option',         ao_get_option_prototype)]

#PAOOPTION = POINTER(ao_option)
#PPAOOPTION = POINTER(PAOOPTION)

# global functions
def log(loglevel, msg):  
  xbmc.log("### [%s] - %s" % ('AirTunes',msg,),level=loglevel ) 
 
def audiooutput_initialize():
  pass
 
def audiooutput_play(device, output_samples, num_bytes):
  if not g_pipesManager.exists(AO_PIPE_NAME):
    return 0
#  NUM_OF_BYTES = 64
#  sentBytes = 0
#  buf[NUM_OF_BYTES];
  
#  while sentBytes < num_bytes:
#    chunkSize = NUM_OF_BYTES
#    if sentBytes < NUM_OF_BYTES:
#      chunkSize = num_bytes - sentBytes
#    memcpy(buf, (char*) output_samples + sentBytes, chunkSize);
#  log(xbmc.LOGDEBUG,"num_bytes: " + str(num_bytes))
  if not g_pipesManager.write(AO_PIPE_NAME, string_at(output_samples,num_bytes)):
    return 0;

#    sentBytes += n;
  return 1;

def audiooutput_default_driver_id():
  return 0

def fourcc(name):
  return String(name, 4)

def audiooutput_open_live(driver_id, format, option):
  if not g_pipesManager.openPipeForWrite(AO_PIPE_NAME):
    log(xbmc.LOGERROR,"error on pipe open")
    return None
  
  g_pipesManager.setOpenThreshold(AO_PIPE_NAME, 0)
  sampleFormat = format.contents
  
  buff = struct.pack('ccccIIIIQ','B','X','A',' ',BXA_PACKET_TYPE_FMT,sampleFormat.channels,sampleFormat.rate,sampleFormat.bits,0)
  if not g_pipesManager.write(AO_PIPE_NAME, buff):
    log(xbmc.LOGERROR, "error wryting BXA header to pipe")
    return None

  xbmc.Player(xbmc.PLAYER_CORE_PAPLAYER).stop()
#todo fixme
#  CFileItem item;

#  if audiooutput_get_option(option, "artist"):
#    item.GetMusicInfoTag()->SetArtist(ao_get_option(option, "artist"));

#  if audiooutput_get_option(option, "album"):
#    item.GetMusicInfoTag()->SetAlbum(ao_get_option(option, "album"));

#  if audiooutput_get_option(option, "name"):
#    item.GetMusicInfoTag()->SetTitle(ao_get_option(option, "name"));
  listitem = xbmcgui.ListItem()
  listitem.setInfo('music', {'title' : 'Streaming'})
  listitem.setProperty('mimetype', 'audio/x-xbmc-pcm')
  xbmc.Player(xbmc.PLAYER_CORE_PAPLAYER).play(AO_PIPE_NAME, listitem)
  xbmc.executebuiltin("ActivateWindow(WINDOWVISUALISATION)")
  # return 1 here null pointer would lead to abort in libshairport (this is a pointe with adr 0x1 - it wont
  # be accessed inlibshairport but only passed around without a sense (refactor of libshairport will get rid)
  # of it
  return 1

def audiooutput_close(device):
  #fix airplay video for ios5 devices
  #on ios5 when airplaying video
  #the client first opens an airtunes stream
  #while the movie is loading
  #in that case we don't want to stop the player here
  #because this would stop the airplaying video
  if xbmc.Player(xbmc.PLAYER_CORE_PAPLAYER).isPlaying():
    xbmc.executebuiltin('PlayerControl(Stop)')
    log(xbmc.LOGDEBUG, "AirPlay not running - stopping player");
  else:
    log(xbmc.LOGDEBUG, "AirPlay video running - player isn't stopped");
  g_pipesManager.setEof(AO_PIPE_NAME)
  g_pipesManager.flush(AO_PIPE_NAME)
  g_pipesManager.closePipe(AO_PIPE_NAME)

  return 0

# -- Device Setup/Playback/Teardown --
def audiooutput_append_option(options, key, value):
  g_options[key] = value
  return 1;

def audiooutput_free_options(options):
  g_options.clear()

def audiooutput_get_option(options, key):
  if key in g_options:
    return g_options[key]
  return None

