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


from optparse import OptionParser,OptionGroup

# -=-[CONFIG]-=-
photo_extensions    = [".jpg",".jpeg",".nef", ".mov", ".mp4"]
exiftool='/usr/bin/exiftool'

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


# -=-[Get Opts]-=-
def getargs():
    photopath   = ''
    sourcepath  = ''
    epilogue    = '    '
    outputpath  = ''
    logfile     = 'None'
    photonum    = 0
    photodate   = False
    igoutput    = False

    usage   = "usage: ijones_photo_cp.py [options] [-p PHOTO PATH] [-s SOURCE] [-o OUTPUT] "
    version = "IJones Photo CP 0.2beta"
    #parser.set_defaults(dryrun=True)

    parser = OptionParser(conflict_handler="resolve", usage = usage, version = version, epilog = epilogue)
    parser.add_option("-p", "--photo-path",
                            dest="photopath",
                                    help="path of the photos database for the last serial number discovery", metavar = "DIR")
    parser.add_option("-s", "--source-path",
                            dest="sourcepath", default='',
                                    help="path of the source of the photo to be copied", metavar="DIR")
    parser.add_option("-o", "--output-path",
                            dest="outputpath", default='',
                                    help="path of th copied photos destination", metavar="DIR")
    parser.add_option("--force-serial",
                            dest="photonum",
                                    help="force initial serial photo number [default: 1]", metavar="NUM")
    parser.add_option("--ignore-output",
                            action="store_true", dest="igoutput", default=False,
                                    help="force to ignore the serial photo numbers might be on the outputh path. WARNING: some file might be overwritten")

    egroup = OptionGroup(parser,"EXIF Option",
                               "EXIF handler options (require libimage-exiftool-perl)")
    egroup.add_option("--add-photo-date",
                            action="store_true", dest="photodate", default=False,
                                    help="add the date of the photo in YYYYMMDD format, the final file name will be <serial>_<date>_<original>")

    dgroup = OptionGroup(parser,"Debug Options")
    dgroup.add_option("--logfile",
                            dest="logfile",
                                    help="enable debug and set the logfile name",  metavar="FILE")
    parser.add_option_group(egroup)
    parser.add_option_group(dgroup)

    (options, args) = parser.parse_args()

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        sys.exit(1)

    return options.photopath, options.sourcepath, options.outputpath, options.logfile, options.photonum, options.photodate, options.igoutput


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
                    if photodate != '':
                        sname       = str(nphoto) + '_' + photodate + '_' + name
                    else:
                        sname   = str(nphoto) + '_' + name
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
    cmd = exiftool + " -d '%Y%m%d' -DateTimeOriginal -S -s " + '"' + fname+'"'
    pdate, err = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
    photodate = ''
    try:
        if isinstance(int(pdate[:8]), int):
            photodate = pdate[:8]
    except:
        pass

    return photodate

# -=-[Driver]-=-
if __name__ == "__main__":
    photo_path, source_path, output_path, logfile, photonum, photodate, igoutput  = getargs()

    if logfile != None:
        logging.basicConfig(filename=logfile,format='%(asctime)s %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')

    if not os.path.exists(photo_path):
        photonum = 0
        print bcolors.green+'>>> '+bcolors.red+'WARNING: '+bcolors.green+'Photo path not found!!!'
        logging.debug("Photo path not found %s" % photo_path)

    if not os.path.exists(source_path):
        print bcolors.green+'>>> '+bcolors.red+'CRITICAL: '+bcolors.green+'Source path not found!!!'
        logging.debug("Source path not found %s" % source_path)
        sys.exit(2)
    elif not os.path.isdir(source_path):
        print bcolors.green+'>>> '+bcolors.red+'CRITICAL: '+bcolors.green+'Source path is not a folder!!!'
        logging.debug("Source path is not a folder %s" % source_path)
        sys.exit(2)

    if not os.path.exists(output_path):
        print bcolors.green+'>>> '+bcolors.red+'CRITICAL: '+bcolors.green+'Output path not found!!!'
        logging.debug("Output path not found %s" % output_path)
        sys.exit(2)
    elif not os.path.isdir(output_path):
        print bcolors.green+'>>> '+bcolors.red+'CRITICAL: '+bcolors.green+'Output path is not a folder!!!'
        logging.debug("Output path is not a folder %s" % output_path)
        sys.exit(2)

    if photonum == None:
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



