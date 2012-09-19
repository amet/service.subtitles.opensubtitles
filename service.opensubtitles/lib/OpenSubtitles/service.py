# -*- coding: utf-8 -*- 

import os
import sys
import xbmc
import urllib
import struct
import xbmcvfs
import xmlrpclib

__scriptname__ = sys.modules[ "__main__" ].__scriptname__

BASE_URL_XMLRPC = u"http://api.opensubtitles.org/xml-rpc"


class OSDBServer:

  def __init__( self, *args, **kwargs ):
    self.server = xmlrpclib.Server( BASE_URL_XMLRPC, verbose=0 )
    login = self.server.LogIn("", "", "en", __scriptname__.replace(" ","_"))    
    self.osdb_token  = login[ "token" ]

  def mergesubtitles( self ):
    self.subtitles_list = []
    if( len ( self.subtitles_hash_list ) > 0 ):
      for item in self.subtitles_hash_list:
        if item["format"].find( "srt" ) == 0 or item["format"].find( "sub" ) == 0:
          self.subtitles_list.append( item )

    if( len ( self.subtitles_list ) > 0 ):
      self.subtitles_list.sort(key=lambda x: [not x['sync'],x['lang_index']])

  def searchsubtitles( self, srch_string, languages, hash_search, _hash = "000000000", size = "000000000"):
    msg                      = ""
    lang_index               = 3
    searchlist               = []
    self.subtitles_hash_list = []
  
    log( __name__ ,"Token:[%s]" % str(self.osdb_token))
  
    try:
      if ( self.osdb_token ) :
        if hash_search:
          searchlist.append({'sublanguageid':','.join(languages), 'moviehash':_hash, 'moviebytesize':str( size ) })
        searchlist.append({'sublanguageid':','.join(languages), 'query':srch_string })
        search = self.server.SearchSubtitles( self.osdb_token, searchlist )
        if search["data"]:
          for item in search["data"]:
            if item["ISO639"]:
              lang_index=0
              for user_lang_id in languages:
                if user_lang_id == item["ISO639"]:
                  break
                lang_index+=1
              flag_image = "flags/%s.gif" % item["ISO639"]
            else:                                
              flag_image = "-.gif"

            if str(item["MatchedBy"]) == "moviehash":
              sync = True
            else:                                
              sync = False

            self.subtitles_hash_list.append({'lang_index'    : lang_index,
                                             'filename'      : item["SubFileName"],
                                             'link'          : item["ZipDownloadLink"],
                                             'language_name' : item["LanguageName"],
                                             'language_flag' : flag_image,
                                             'language_id'   : item["SubLanguageID"],
                                             'ID'            : item["IDSubtitleFile"],
                                             'rating'        : str(int(item["SubRating"][0])),
                                             'format'        : item["SubFormat"],
                                             'sync'          : sync,
                                             'hearing_imp'   : int(item["SubHearingImpaired"]) != 0
                                             })
            
    except:
      msg = "Error Searching For Subs"
    
    self.mergesubtitles()
    return self.subtitles_list, msg

  def download(self, ID, dest):
     try:
       import zlib, base64
       down_id=[ID,]
       result = self.server.DownloadSubtitles(self.osdb_token, down_id)
       if result["data"]:
         local_file = open(dest, "w" + "b")
         d = zlib.decompressobj(16+zlib.MAX_WBITS)
         data = d.decompress(base64.b64decode(result["data"][0]["data"]))
         local_file.write(data)
         local_file.close()
         return True
       return False
     except:
       return False

def log(module, msg):
  xbmc.log((u"### [%s] - %s" % (module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG ) 

def hashFile(file_path):
    longlongformat = 'q'  # long long
    bytesize = struct.calcsize(longlongformat)
    f = xbmcvfs.File(file_path)
    
    filesize = f.size()
    hash = filesize
    
    if filesize < 65536 * 2:
        return "SizeError"
    
    buffer = f.read(65536)
    f.seek(max(0,filesize-65536),0)
    buffer += f.read(65536)
    f.close()
    for x in range((65536/bytesize)*2):
        size = x*bytesize
        (l_value,)= struct.unpack(longlongformat, buffer[size:size+bytesize])
        hash += l_value
        hash = hash & 0xFFFFFFFFFFFFFFFF
    
    returnHash = "%016x" % hash
    return filesize,returnHash


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

def search_subtitles( item ):
  ok = False
  hash_search = False
  if len(item['tvshow']) > 0:                                            # TvShow
    OS_search_string = ("%s S%.2dE%.2d" % (item['tvshow'],
                                           int(item['season']),
                                           int(item['episode']),)
                                          ).replace(" ","+")      
  else:
    if str(item['year']) == "":
      item['title'], item['year'] = xbmc.getCleanMovieTitle( item['title'] )

    OS_search_string = item['title'].replace(" ","+")
    
  log( __name__ , "Search String [ %s ]" % (OS_search_string,))     
 
  if item['temp'] : 
    hash_search = False
    file_size   = "000000000"
    SubHash     = "000000000000"
  else:
    try:
      file_size, SubHash   = hashFile(item['file_original_path'])
      log( __name__ ,"xbmc module hash and size")
      hash_search = True
    except:  
      file_size   = ""
      SubHash     = ""
      hash_search = False
  
  if file_size != "" and SubHash != "":
    log( __name__ ,"File Size [%s]" % file_size )
    log( __name__ ,"File Hash [%s]" % SubHash)
  
  log( __name__ ,"Search by hash and name %s" % (os.path.basename( item['file_original_path'] ),))
  item['subtitles_list'], item['msg'] = OSDBServer().searchsubtitles( OS_search_string, item['3let_language'], hash_search, SubHash, file_size  )

# 2 below items need to be returned to main script
# item['subtitles_list'] list of all subtitles found, needs to include below items. see searchsubtitles above for more info
#                        "language_name"
#                        "filename"
#                        "rating"
#                        "language_flag"
# item['msg'] message notifying user of any errors

  return item

######## Standard Download function ###########
# as per search_subtitles explanation
#
# 3 below items are needed as a result
# item['zipped']   - is subtitle in zip?
# item['file']     - file where unzipped subtitle is saved ,
#                    main script will remame it and copy to 
#                    correct location(will be ignored if item['zipped'] is true
# item['language'] - language of the subtitle file. 
#                    it can be Full language name, 2 letter(ISO 639-1) or 3 letter(ISO 639-2)
#                    e.g English or en or eng
#                    e.g Serbian or sr or scc
###############################################
def download_subtitles (item):
  item['file'] = os.path.join(item['tmp_sub_dir'], "%s.srt" % item['subtitles_list'][item['pos']][ "ID" ])
  result = OSDBServer().download(item['subtitles_list'][item['pos']][ "ID" ], item['file'])
  if not result:
    import urllib
    log( __name__,"Download Using http://")
    urllib.urlretrieve(item['subtitles_list'][item['pos']][ "link" ],item['zip_subs'])  
  else:
    log( __name__,"Download Using XMLRPC")
  item['zipped'] = not result
  item['language'] = item['subtitles_list'][item['pos']][ "language_name" ]
  
  return item    
