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

AUTH_DIGEST_REALM                 = 'AirPlay'
AUTH_DIGEST_USERNAME              = 'AirPlay'

AIRPLAY_ZEROCONF_HANDLE     			= "servers.airplay"
AIRPLAY_ZEROCONF_PROTO      			= "_airplay._tcp"
AIRPLAY_ZEROCONF_RECORD_SRCVERS   = "101.28"
AIRPLAY_ZEROCONF_RECORD_FEATURES  = "0x77"
AIRPLAY_ZEROCONF_RECORD_MODEL     = "AppleTV2,1"

#airtunes zeroconf definitions
AIRTUNES_ZEROCONF_HANDLE   				= "servers.airtunes"
AIRTUNES_ZEROCONF_PROTO     			= "_raop._tcp"
AIRTUNES_ZEROCONF_RECORD_CN 			= "0,1"
AIRTUNES_ZEROCONF_RECORD_CH 			= "2"
AIRTUNES_ZEROCONF_RECORD_EK 			= "1"
AIRTUNES_ZEROCONF_RECORD_ET 			= "0,1"
AIRTUNES_ZEROCONF_RECORD_SV 			= "false"
AIRTUNES_ZEROCONF_RECORD_TP 			= "UDP"
AIRTUNES_ZEROCONF_RECORD_SM 			= "false"
AIRTUNES_ZEROCONF_RECORD_SS 			= "16"
AIRTUNES_ZEROCONF_RECORD_SR 			= "44100"
AIRTUNES_ZEROCONF_RECORD_PW 			= "false"
AIRTUNES_ZEROCONF_RECORD_VN 			= "3"
AIRTUNES_ZEROCONF_RECORD_TXTVERS 	= "1"

PLAYBACK_INFO = '<?xml version="1.0" encoding="UTF-8"?>\r\n\
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\r\n\
<plist version="1.0">\r\n\
<dict>\r\n\
<key>duration</key>\r\n\
<real>%f</real>\r\n\
<key>loadedTimeRanges</key>\r\n\
<array>\r\n\
\t\t<dict>\r\n\
\t\t\t<key>duration</key>\r\n\
\t\t\t<real>%f</real>\r\n\
\t\t\t<key>start</key>\r\n\
\t\t\t<real>0.0</real>\r\n\
\t\t</dict>\r\n\
</array>\r\n\
<key>playbackBufferEmpty</key>\r\n\
<true/>\r\n\
<key>playbackBufferFull</key>\r\n\
<false/>\r\n\
<key>playbackLikelyToKeepUp</key>\r\n\
<true/>\r\n\
<key>position</key>\r\n\
<real>%f</real>\r\n\
<key>rate</key>\r\n\
<real>%d</real>\r\n\
<key>readyToPlay</key>\r\n\
<true/>\r\n\
<key>seekableTimeRanges</key>\r\n\
<array>\r\n\
\t\t<dict>\r\n\
\t\t\t<key>duration</key>\r\n\
\t\t\t<real>%f</real>\r\n\
\t\t\t<key>start</key>\r\n\
\t\t\t<real>0.0</real>\r\n\
\t\t</dict>\r\n\
</array>\r\n\
</dict>\r\n\
</plist>\r\n\r\n'

PLAYBACK_INFO_NOT_READY = '<?xml version="1.0" encoding="UTF-8"?>\r\n\
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\r\n\
<plist version="1.0">\r\n\
<dict>\r\n\
<key>readyToPlay</key>\r\n\
<false/>\r\n\
</dict>\r\n\
</plist>\r\n\r\n'

SERVER_INFO = '<?xml version="1.0" encoding="UTF-8"?>\r\n\
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\r\n\
<plist version="1.0">\r\n\
<dict>\r\n\
<key>deviceid</key>\r\n\
<string>%s</string>\r\n\
<key>features</key>\r\n\
<integer>119</integer>\r\n\
<key>model</key>\r\n\
<string>AppleTV2,1</string>\r\n\
<key>protovers</key>\r\n\
<string>1.0</string>\r\n\
<key>srcvers</key>\r\n\
<string>' + AIRTUNES_ZEROCONF_RECORD_TXTVERS + '</string>\r\n\
</dict>\r\n\
</plist>\r\n\r\n'

EVENT_INFO = '<?xml version="1.0" encoding="UTF-8"?>\n\r\
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\r\n\
<plist version="1.0">\r\n\
<dict>\r\n\
<key>category</key>\r\n\
<string>video</string>\r\n\
<key>state</key>\r\n\
<string>%s</string>\r\n\
</dict>\r\n\
</plist>\r\n\r\n'