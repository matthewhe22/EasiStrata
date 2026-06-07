#!/usr/bin/env python
# coding: utf-8



import os
import re
import shutil



def parseFilePath(filename):
    if not doesFileExist(filename):
        raise Exception('File "{}" does not exists'.format(filename))
    full_path = os.path.abspath(filename)
    arr_path = full_path.split(os.sep)
    root_dir = os.sep.join(arr_path[:-1])
    filename = arr_path[-1]
    return root_dir,filename
def parseFileName(filename):
    arr_filename=filename.split('.')
    name='.'.join(arr_filename[:-1])
    extension=arr_filename[-1]
    #If there is no '.' in the name of file
    if len(arr_filename)==1:
        name=filename
        extension=''
    return name,extension


def correctPath(path):
    path = path.strip()
    # Remove separator from end of path
    while path.endswith(os.sep):
        path = path[:-1]
    return path
def checkIfPathExists(path):
    return os.path.isdir(r"{}".format(path))
def isFile(file):
    return os.path.exists(file) and os.path.isfile(file)
def isDirectory(path):
    return os.path.exists(path) and os.path.isdir(path)
def doesFileExist(filename):
    return isFile(filename)
def getFilenameVersion(filename):
    name,extension = parseFileName(filename)
    m = re.match("(.*_)(\d+)$",name)
    if m:
        verNumber = int(m.group(2))+1
        name=m.group(1)+str(verNumber)
    else:
        name=name+'_1'
    if extension!='':
        filename = '.'.join([name,extension])
    else:
        filename = name
    return filename
def copyFile(srcname,dstpath,overwrite=False,filename=None):
    if filename is None:
        filename=srcname.split(os.sep)[-1]
    if not os.path.exists(os.path.join(dstpath,filename)):
        # print('Copying file',srcname,'into',dstpath)
        shutil.copy(srcname,os.path.join(dstpath,filename))
    elif overwrite:
        # print('Overwriting file',srcname,'into',dstpath)
        shutil.copy(srcname,os.path.join(dstpath,filename))
    else:
        filename=getFilenameVersion(filename)
        copyFile(srcname,dstpath,overwrite,filename)
def createDirFiles(rsrc,dstpath,extensions=[],overwrite=False):
    srcwalk = os.walk(rsrc)
    tmpsrcwalk = next(srcwalk)
    root,dirs,files = tmpsrcwalk
    #CREATE ONLY FOLDERS FROM CURRENT FOLDER
    for folder in dirs:
        newfolder = os.path.join(dstpath,folder)
        if not checkIfPathExists(newfolder):
            print('Creating folder',folder,'in',dstpath)
            os.mkdir(newfolder)
        createDirFiles(os.path.join(rsrc,folder),os.path.join(dstpath,folder),extensions,overwrite)
    #COPY ONLY FILES FROM CURRENT FOLDER 
    for name in files:
        hasExtension = len(extensions)==0
        for extension in extensions:
            if name.lower().endswith(extension.lower()):
                hasExtension = True
                break
        if hasExtension:
            copyFile(os.path.join(root,name),dstpath,overwrite)
def getAbsoluteFilepathFromDirectory(path,patterns=[]):
    list_of_files = []
    path = correctPath(path)
    if type(patterns)!=list:
        raise Exception('Patterns ({}) should be a list'.format(patterns))
    if not checkIfPathExists(path):
        raise Exception('Source folder {} does not exist'.format(path))
    #COPY ONLY FILES RECURSIVELY FROM srcpath
    for root,dirs,files in os.walk(path):
        for name in files:
            if name.startswith('~'):
                continue
            hasPattern = len(patterns)==0
            for pattern in patterns:
                if pattern != None and pattern in name:
                    hasPattern = True
                    break
            if hasPattern:
                list_of_files.append(os.path.join(root,name))
    return list_of_files
def transferFiles(srcpath,dstpath,extensions=[],withFolder=True,overwrite=False):
    srcpath = correctPath(srcpath)
    dstpath = correctPath(dstpath)
    if type(extensions)!=list:
        raise Exception('Extensions ({}) should be a list'.format(extensions))
    if not checkIfPathExists(srcpath):
        raise Exception('Source folder {} does not exist'.format(srcpath))
    if not checkIfPathExists(dstpath):
        raise Exception('Destination folder {} does not exist'.format(dstpath))
    if withFolder:
        createDirFiles(srcpath,dstpath,extensions,overwrite)
    else:
        #COPY ONLY FILES RECURSIVELY FROM srcpath
        for root,dirs,files in os.walk(srcpath):
            for name in files:
                hasExtension = len(extensions)==0
                for extension in extensions:
                    if name.lower().endswith(extension.lower()):
                        hasExtension = True
                        break
                if hasExtension:
                    copyFile(os.path.join(root,name),dstpath,overwrite)
    print('Files transfered from',srcpath,'to',dstpath)




