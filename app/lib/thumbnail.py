#!/usr/bin/env python
import os
from PIL import Image, ImageChops, ImageOps
from tornado.options import options
import logging

thumbnail_size_list=[('xs',32,32),('s',64,64),('m',128,128),('l',640,480),('xl',1024,768)]

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

def _removeThumbnails(doc_id):
    thumbnail_subfolder = getThumbnailFolderByDocId(doc_id)
    for size_name,w,h in thumbnail_size_list:
        thumbnail_path = '%s/thumbnails/%s/%s/%s.png' % (options.storage_access_point,thumbnail_subfolder,size_name,doc_id)
        logging.info("remove thumbnails at real_path: %s ... ", thumbnail_path)
        if os.path.isfile(thumbnail_path):
            os.unlink(thumbnail_path)

def _generateThumbnails(src_file, doc_id):
    filename, file_extension = os.path.splitext(src_file)
    thumbnail_subfolder = getThumbnailFolderByDocId(doc_id)
    size_list=[('xs',32,32),('s',64,64),('m',128,128),('l',640,480),('xl',1024,768)]
    for size_name,w,h in thumbnail_size_list:
        thumbnail_path = '%s/thumbnails/%s/%s/%s.png' % (options.storage_access_point,thumbnail_subfolder,size_name,doc_id)
        logging.info("generateThumbnails at path: %s ... ", thumbnail_path)
        size_w_h = (w,h)
        makeThumb(src_file,thumbnail_path,size=size_w_h,pad=True)

def getThumbnailFolderByDocId(doc_id):
    #for uuid format.
    #thumbnail_subfolder = doc_id[:6]
    thumbnail_subfolder = str(doc_id/100)
    return thumbnail_subfolder

def isSupportedFormat(f_in):
    filename, file_extension = os.path.splitext(f_in)
    supported_list = ['.bmp','.eps','.gif','.im','.jpeg','.jpg','.msp','.pcx','.png','.ppm','.tif','.tiff','.webp','.xbm']
    ret_val = False
    #logging.info("file_extension: %s ... ", file_extension)
    if not file_extension is None:
        if file_extension.lower() in supported_list:
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
        logging.info("makeThumb thumbnails at real_path: %s to %s ... ", f_in, f_out)
        if os.path.exists(f_out):
            # force delete output file.
            os.unlink(f_out)
        else:
            # path not found, but we need a folder...
            prepareThumbnailsFolder(f_out)

        # start to open file.
        image = Image.open(f_in)
        image.thumbnail(size, Image.ANTIALIAS)
        image_size = image.size

        thumb = None
        if pad:
            thumb = image.crop( (0, 0, size[0], size[1]) )

            offset_x = max( (size[0] - image_size[0]) / 2, 0 )
            offset_y = max( (size[1] - image_size[1]) / 2, 0 )

            thumb = ImageChops.offset(thumb, offset_x, offset_y)

        else:
            thumb = ImageOps.fit(image, size, Image.ANTIALIAS, (0.5, 0.5))

        thumb.save(f_out)
    else:
        # file not found error handle
        pass