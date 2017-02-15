#!/usr/bin/env python
import os
from PIL import Image, ImageChops, ImageOps
from tornado.options import options
import logging

thumbnail_size_list=[(32,32),(64,64),(128,128),(640,480),(1024,768)]

_orientation_to_rotation = {
    3: 180,
    6: 90,
    8: 270
}

_filters_to_pil = {
    "antialias": Image.ANTIALIAS,
    "bicubic": Image.BICUBIC,
    "bilinear": Image.BILINEAR,
    "nearest": Image.NEAREST
}

_formats_to_pil = {
    "gif": "GIF",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "tiff": "TIFF"
}


# todo: 
#   my doc_id may conflict(duplicate) between different pool. 
#   (very very hard to conflict, ignore to process this issue)
#
# PS: my thumbnails only generate on owner's pool.

# who to handle, a shared folder content 10 member, non-owner upload a file in shared folder?
# Question 1: how to show the metadata? (all member online / some member offline)
#   1-1: for owner
#   1-2: for others 8 member.
#   1-3: for creator.
# Question 2: how to show the delta? (all member online / some member offline)
#   2-1: for owner
#   2-2: for others 8 member.
#   2-3: for creator.
# Question 4: how to show the thumbnail? (all member online / some member offline)
#   3-1: for owner
#   3-2: for others 8 member.
#   3-3: for creator.

# Question: why not able to upload file to shared folder if owner is offline.
# Question: is there some important file in shared folder and owner is offline, but user want to access?

# Conclustion: My Prefer Active-Active mode for shared folder, 
# My case is: 
#   (1) 10 member join a shared folder, user-01 is owner, user-02 to user-10 is non-owner.
#   (2) user-02 upload a file in shared folder.
#   (3) each subscriber need to get the pool's history to sync their sync pool.

# Question: what if user have two HDD (HD-A is 4TB, HD-B is 2TB), 
#           and user is connecting to 2TB, and 2TB don't has any space able to upload?

# Sync files to other Transporters located anywhere in the world for offsite backup or to share files with friends and colleagues.
# I think we should focus on sync and backup user's data and let user eazy to learn and to share files.

# < Simplify Sharing >
# -- Enable easy yet private collaboration with colleagues and clients
# -- Files sync automatically so everyone always has the latest version

# Question: what if user-A and user-B collaborate in shared folder, and user-B is over-quota.
#         : is user-B able to use more space after buy a new device?

# delta/metadata/thumbnail is a "pull" or "push" problem.
# Who should generate the delta/metadata/thumbnail, if owner is offline, thumbnail is not able to show?
# This is very important question for design!
# if owner is offline and not able to show thumbnail, then delta/metadata/thumbnail just need one part.

# base on A-A mode, (owner offline able to access)
# I think shared folder(pool) is master, each subscriber's pool is slave.
# each member make events on shared pool, after this step, subscriber sync a pool's delta to owner

# the probability of relay mode on home user's 2 tera-bytes server?

# my conclustion:
# case 1: owner's pool.
# every event/metadata/thumbnail generate first copy on creator's pool.
# check the path is on share folder, generate a second copy on share folder pool.

# case 2: shared folder pool:
# check the shared folder

# there are 2 way to save thumbnail, 
#   1. deduplate, all same file only one copy.
#       convient for insert event,
#       when to delete thumbnail? 
#           (1-1) each delete time to check. 
#           (1-2) schedule to batch delete. (I like this.)
#   2. duplated, all same file many copy.
#       convient for delete event.
#       need a recurcive to scan new copied files.

def getThumbnailFolder(doc_id):
    thumbnail_subfolder = str(doc_id/1000) + "/" + str(doc_id % 1000)
    thumbnail_folder = '%s/thumbnails/%s/%s' % (options.storage_access_point,thumbnail_subfolder,doc_id)
    return thumbnail_folder

def _removeThumbnails(doc_id):
    thumbnail_folder = getThumbnailFolder(doc_id)
    if os.path.exists(thumbnail_folder):
        _deletePath(thumbnail_folder)

# [TODO]:
# delete fail, but file locked.
def _deletePath(real_path):
    import shutil
    #logging.info("delete Thumbnails at path: %s ... ", real_path)
    if os.path.isfile(real_path):
        os.unlink(real_path)
    else:
        for root, dirs, files in os.walk(real_path):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        shutil.rmtree(real_path)

def _generateThumbnails(src_file, doc_id):
    if isSupportedFormat(src_file):
        filename, file_extension = os.path.splitext(src_file)
        thumbnail_folder = getThumbnailFolder(doc_id)
        for w,h in thumbnail_size_list:
            filename = "w%sh%s%s" % (str(w), str(h),file_extension)
            thumbnail_path = os.path.join(thumbnail_folder,filename)
            #logging.info("generateThumbnails at path: %s ... ", thumbnail_path)
            makeThumb(src_file,thumbnail_path,size=(w,h),pad=True)

def _getThumbnailPath(doc_id, size_name, file_extension):
    thumbnail_folder = getThumbnailFolder(doc_id)
    new_filename = "%s%s" % (size_name,file_extension)
    thumbnail_path = os.path.join(thumbnail_folder,new_filename)
    return thumbnail_path

def isSupportedFormat(f_in):
    filename, file_extension = os.path.splitext(f_in.lower())
    supported_list = ['.bmp','.eps','.gif','.im','.jpeg','.jpg','.msp','.pcx','.png','.ppm','.tif','.tiff','.webp','.xbm']
    ret_val = False
    #logging.info("file_extension: %s ... ", file_extension)
    if not file_extension is None:
        if file_extension in supported_list:
            ret_val = True
        else:
            pass
            #logging.info("file_extension not is list: %s ... ", file_extension)
    else:
        pass
        #logging.info("file_extension is none: %s ... ", file_extension)
    return ret_val

def prepareThumbnailsFolder(f_out):
    head, tail = os.path.split(f_out)
    if not os.path.exists(head):
        try:
            os.makedirs(head)
        except OSError as exc: 
            pass

def makeThumb(f_in, f_out, size=(64,64), pad=False):
    if os.path.exists(f_in):
        #logging.info("makeThumb thumbnails at real_path: %s to %s ... ", f_in, f_out)
        if os.path.exists(f_out):
            # force delete output file.
            #[TODO]
            # file locked!
            os.unlink(f_out)
        else:
            # path not found, but we need a folder...
            prepareThumbnailsFolder(f_out)

        filename, file_extension = os.path.splitext(f_in.lower())
        if file_extension.startswith('.'):
            file_extension = file_extension[1:]
        _orig_format = _formats_to_pil.get(file_extension)

        # start to open file.
        image = Image.open(f_in)
        if _orig_format == "JPEG":
            image = autorotate(image)
        
        image_size = image.size

        thumb = None
        if pad:
            shorter = image_size[0] if image_size[0] < image_size[1] else image_size[1]

            offset_x = max( (image_size[0] - shorter) / 2, 0 )
            offset_y = max( (image_size[1] - shorter) / 2, 0 )

            thumb = image.crop( (offset_x, offset_y, offset_x + shorter, offset_y + shorter) )

            thumb.thumbnail(size, Image.ANTIALIAS)
            #[TODO]:
            # .thumbnail() will alway make square image,
            # to support 640x480 & 1024x768 need use .resize()
            #thumb = thumb.resize(size)
        else:
            thumb = ImageOps.fit(image, size, Image.ANTIALIAS, (0.5, 0.5))

        try:
            thumb.save(f_out)
        except IOError as e:
            # no free space or ...
            errorMessage = 'unable to save thumbnail'
            logger.error(errorMessage)        
    else:
        # file not found error handle
        pass


def autorotate(img):
    deg = 0
    exif = None
    try:
        exif = img._getexif() or dict()
        deg = _orientation_to_rotation.get(exif.get(274, 0), 0)
    except Exception:
        logger.warn('unable to parse exif')

    img = img.rotate(360 - int(deg))
    return img

