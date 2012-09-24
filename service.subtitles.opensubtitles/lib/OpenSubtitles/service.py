# -*- coding: utf-8 -*- 

import os
import sys
import xbmc
import urllib
import xbmcvfs
import xbmcaddon

from OSUtilities import OSDBServer, log, hashFile

__addon__ = xbmcaddon.Addon('service.subtitles.opensubtitles')

######## Standard Search function ###########
# 'item' has everything thats needed for search parameters, look in script.subtitles.main/gui.py for detailed info
# below list might be incomplete
#
#    item['file_original_path']
#    item['year']
#    item['season']
#    item['episode']
#    item['tvshow']
#    item['title']
# anything needed for download can be saved here and later retreived in 'download_subtitles' function
#############################################

def Search( item ):
  item['msg'] = ""
    
 
  search_data = OSDBServer().searchsubtitles(item)

  if search_data != None:
    for item_data in search_data:
      item['subtitles_list'].append({'filename'       : item_data["SubFileName"],
                                      'link'          : item_data["ZipDownloadLink"],
                                      'language'      : item_data["LanguageName"],
                                      'ID'            : item_data["IDSubtitleFile"],
                                      'rating'        : "%.1d" % float(item_data["SubRating"]),
                                      'format'        : item_data["SubFormat"],
                                      'sync'          : str(item_data["MatchedBy"]) == "moviehash",
                                      'hearing_imp'   : int(item_data["SubHearingImpaired"]) != 0
                                      })
  else:                                    
    item['msg'] = __addon__.getLocalizedString(610)
    
  item['subtitles_list'].sort(key=lambda x: [not x['sync'],x['language']])  
# item['subtitles_list'] needs to be returned to main script
# list of all subtitles found, needs to include below items. see searchsubtitles above for more info
#                        "language"
#                        "filename"
#                        "rating"
  return item

######## Standard Download function ###########
# as per search_subtitles explanation
#
# we need to return list of subtitles to main script, if list contains more than one subtitle file,
#  it needs to be sorted so that CD1 is first, CD2 second...
# items in list of subtitles can be:
#                           download url for subtitle(uncompressed),
#                           local file,
#                           network file(smb, nfs, afp),
#                           file in zip or rar archive(path/to/zip.zip/subtitle_file.srt)
###############################################
def Download(item):
  subtitle_list = []
  exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
  if item['stack']: ## we only want XMLRPC download if movie is not in stack,
                    ## you can only retreive multiple subs in zip
    result = False
  else:
    subtitle = os.path.join(item['tmp_sub_dir'], item['subtitles_list'][item['pos']][ "filename" ])
    result = OSDBServer().download(item['subtitles_list'][item['pos']][ "ID" ], subtitle)
  if not result:
    log( __name__,"Download Using HTTP")
    zip = os.path.join( item['tmp_sub_dir'], "OpenSubtitles.zip")
    f = urllib.urlopen(item['subtitles_list'][item['pos']][ "link" ])
    with open(zip, "wb") as subFile:
      subFile.write(f.read())
    subFile.close()
    xbmc.sleep(500)
    xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (zip,item['tmp_sub_dir'],)).encode('utf-8'), True)
    for file in xbmcvfs.listdir(zip)[1]:
      file = os.path.join(item['tmp_sub_dir'], file)
      if (os.path.splitext( file )[1] in exts):
        subtitle_list.append(file)
  else:
    subtitle_list.append(subtitle)
    
  if xbmcvfs.exists(subtitle_list[0]):
    return subtitle_list
    
    