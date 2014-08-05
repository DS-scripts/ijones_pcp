#!/usr/bin/python
#
#
# V 0.2b
#

import os
import sys
import shutil
import subprocess
import time
import logging
import smtplib
import getopt


# -=-[CONFIG]-=-
photo_extensions    = [".jpg",".jpeg",".nef", ".mov", ".mp4"]

# -=-[STDOUT Colors]-=-
class bcolors:
    gray             = '\033[1;30m'
    red              = '\033[1;31m'
    green            = '\033[1;32m'
    yellow           = '\033[1;33m'
    blue             = '\033[1;34m'
    magenta          = '\033[1;35m'
    cyan             = '\033[1;36m'
    white            = '\033[1;37m'
    highlightgreen   = '\033[1;42m'
    highlightblue    = '\033[1;44m'
    highlightmagenta = '\033[1;45m'
    highlightcyan    = '\033[1;46m'
    highlightred     = '\033[1;48m'
    reset            = '\033[0m'

def usage ():
    print bcolors.white+' usage: '+bcolors.red+'ijones_photo_cp.py'+bcolors.green+' [-h] [-p PHOTOSPATH] [-s SOURCEPATH] [-o OUTPUTPATH]'
    print '                           [--logfile LOGFILE] [--force-serial SERIALNUM]'
    print '                           [--add-photo-date] [--ignore-output]'
    print ' '+bcolors.white
    print ' optional arguments:'
    print bcolors.green+'    -h --help                 '+bcolors.white+'how this help message and exit'
    print bcolors.green+'    -p --photos-path PATH     '+bcolors.white+'path of the photos database for the last serial'
    print bcolors.green+'                              '+bcolors.white+'number discovery'
    print bcolors.green+'    -s --source-path PATH     '+bcolors.white+'path of the source of the photo to be copied'
    print bcolors.green+'    -o --output-path PATH     '+bcolors.white+'path of th copied photos destination'
    print bcolors.green+'    --logfile LOGFILE         '+bcolors.white+'logfile name'
    print bcolors.green+'    --force-serial SERIALNUM  '+bcolors.white+'force initial serial photo number'
    print bcolors.green+'    --add-photo-date          '+bcolors.white+'add the photo date in the output file name in'
    print bcolors.green+'                              '+bcolors.white+'YYYYMMDD format (require libimage-exiftool-perl)'
    print bcolors.green+'    --ignore-output           '+bcolors.white+'force to ignore the serial photo numbers might'
    print bcolors.green+'                              '+bcolors.white+'be on the outputh path '
    print bcolors.green+'                              '+bcolors.white+'WARNING: some file might be overwritten'
    print bcolors.reset+' '

# -=-[Get Opts]-=-
def getargs(argv):
    photopath   = ''
    sourcepath  = ''
    outputpath  = ''
    logfile     = 'None'
    photonum    = 0
    photodate   = False
    igoutput    = False

    try:
        opts, args = getopt.getopt(argv,"hp:s:o:",["help", "photos-path=","source-path=", "output-path=",
                                                   "logfile=", "force-serial=", "add-photo-date", "ignore-output"])
        if not opts:
            usage ()
            sys.exit(2)
    except getopt.GetoptError as err:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        elif opt in ("-p", "--photos-path"):
            photopath = arg
        elif opt in ("-s", "--source-path"):
            sourcepath = arg
        elif opt in ("-o", "--output-path"):
            outputpath = arg
        elif opt in ("--logfile"):
            logfile = arg
        elif opt in ("--force-serial"):
            photonum = int(arg)
        elif opt in ("--add-photo-date"):
            photodate = True
        elif opt in ("--ignore-output"):
            igoutput = True
        else:
            usage()
            sys.exit(2)

    return photopath, sourcepath, outputpath, logfile, photonum, photodate, igoutput

# -=-[Find Last Serial Photo Num]-=-
def findlastnum (path, opath, pext, igoutput):
    lastnum     = 0
    photofile   = ''
    lnum        = 0
    lnumo       = 0
    sys.stdout.write("\r")
    sys.stdout.write(bcolors.green+">>> Looking for the last photo serial number ... ")

    if not igoutput:
        lnum, pfile = findinfolder(path, pext)
        lnumo, pfileo = findinfolder(opath, pext)
        if lnum > lnumo:
            lastnum = lnum
            photofile = pfile
        else:
            lastnum = lnumo
            photofile = pfileo
    else:
        lastnum, photofile = findinfolder(path, pext)
    print (bcolors.white+" ")
    return lastnum, photofile

#-=-[Find last in a folder]-=-
def findinfolder (path, pext):
    lnum = 0
    pfile = ''
    for root, dirs, files in os.walk(path):
        for name in files:
            ext = os.path.splitext(name)[1]
            if  ext.lower() in pext:
                try:
                    if name[5] == '_':
                        sys.stdout.write("\r")
                        sys.stdout.write(bcolors.green+">>> Looking for the last photo serial number ... ")
                        sys.stdout.write(bcolors.red+"%s" % name)
                        sys.stdout.write(bcolors.white+"                     ")
                        sys.stdout.flush()
                        if strisint(name[:5]):
                            if  int(name[:5]) > lnum:
                                lnum     = int(name[:5])
                                pfile   = name
                except IndexError:
                    pass
    return lnum, pfile

# -=-[Check if the str is a integer]-=-
def strisint(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
# -=-[Copy Photo adding serial number]-=-
def copyphotos (spath, opath, pext, nphoto, pdate):
    for root, dirs, files in os.walk(spath):
        for name in files:
            ext = os.path.splitext(name)[1]
            if ext.lower() in pext:
                fname   = os.path.join(root,name)
                if pdate:
                    photodate   = getphotodate(fname)
                    sname       = str(nphoto) + '_' + photodate + '_' + name
                else:
                    sname   = str(nphoto) + '_' + name

                fsname  = os.path.join(opath,sname)
                sys.stdout.write("\r")
                sys.stdout.write(bcolors.green+"    Coping ")
                sys.stdout.write(bcolors.red+"%13s" % name)
                sys.stdout.write(bcolors.green+" ....................... ")
                sys.stdout.write(bcolors.red+"%s" % sname)
                sys.stdout.write(bcolors.white+"                    ")
                sys.stdout.flush()
                logging.debug(">>> sending copy command %s %s" % (fname, fsname))
                copy(fname,fsname)
                nphoto += 1
                print (bcolors.reset+" ")

# -=-[Copy files]-=-
def copy(src,dst,remove=False):
    logging.debug("copying %s %s" % (src,dst))
    ok = False
    try:
        shutil.copy(src,dst)
        ok = True
    except:
        logging.debug("not copied %s" % (sys.exc_info(),))
    if not ok:
        try:
            logging.debug("trying with %s %s" % (src,dst + "/" + src))
            shutil.copyfile(src,dst + "/" + src)
            ok = True
        except:
            logging.debug<F5>("not copied again. %s" % (sys.exc_info(),))
            for i in os.environ:
                logging.debug("Env: %s: %s" % (i,os.environ[i]))
    if not ok:
        try:
            logging.debug("trying with %s %s" % (src,dst + "/" + src))
            s,e = subprocess.Popen('whoami',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            logging.debug("stdout = %s" % s)
            logging.debug("stderr = %s" % e)
        except:
            logging.debug("not copied again. %s" % (sys.exc_info(),))
            for i in os.environ:
                logging.debug("Env: %s: %s" % (i,os.environ[i]))
    return

def getphotodate(fname):
    cmd = "exiftool -d '%Y%m%d' -DateTimeOriginal -S -s " + fname
    photodate, err = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
    return photodate[:8]

# -=-[Driver]-=-
if __name__ == "__main__":
    photo_path, source_path, output_path, logfile, photonum, photodate, igoutput  = getargs(sys.argv[1:])

    if logfile != None:
        logging.basicConfig(filename=logfile,format='%(asctime)s %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s')

    if not os.path.exists(photo_path):
        photonum = 0
        print bcolors.green+'>>> '+bcolors.red+'WARNING: '+bcolors.green+'Photo path not found!!!'
        logging.debug("Photo path not found %s" % photo_path)
    elif not os.path.exists(source_path):
        print bcolors.green+'>>> '+bcolors.red+'CRITICAL: '+bcolors.green+'Source path not found!!!'
        logging.debug("Source path not found %s" % source_path)
        sys.exit(2)
    elif not os.path.exists(output_path):
        print bcolors.green+'>>> '+bcolors.red+'CRITICAL: '+bcolors.green+'Output path not found!!!'
        logging.debug("Output path not found %s" % output_path)
        sys.exit(2)

    if photonum == 0:
        lastnumphoto, filename = findlastnum(photo_path, output_path, photo_extensions, igoutput)
        numphoto               = lastnumphoto + 1
    else:
        numphoto               = photonum
    sys.stdout.write("\r")
    sys.stdout.write(bcolors.green+">>> Next photo serial number ................... ")
    sys.stdout.write(bcolors.red+"%d" % numphoto)
    print (bcolors.reset+" ")
    copyphotos (source_path, output_path, photo_extensions, numphoto, photodate)
    print bcolors.green+'>>> Done!!!'



