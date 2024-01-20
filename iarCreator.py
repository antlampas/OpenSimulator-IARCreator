# Author: Antlampas
# Creation Date: 2022-09-23
# Version: 1.0
# License: This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

from sys             import argv
from shutil          import copy,copyfileobj
from pathlib         import Path,PosixPath,WindowsPath
from uuid            import uuid4
from datetime        import datetime

import gzip
import re
import tarfile

def makeIarStructure(source,destination,func):
    if not destination.exists() and (str(destination) == argv[2]):
        destination.mkdir(parents=True)
    for f in source.iterdir():
        if f.is_dir():
            destParents = f.relative_to(argv[1])
            dP_new = ""
            for parent in reversed(destination.parents):
                for dP in reversed(destParents.parents):
                    if str(dP).find(str(parent)) >= 0:
                        dP_new += str(dP)
                        break
            dP_new += str(f.stem)
            dP_new = dP_new.replace(".","")
            dest = Path(str(destination)+"/"+str(dP_new)+"__"+str(uuid4()))
            if not dest.exists():
                dest.mkdir(parents=True)
            makeIarStructure(f,dest,func)
        elif f.is_file():
            func(f,argv[2]+'/assets',destination)

def addFile(f,destinationAsset,destinationInventory):
    result = copyAndRename(f,destinationAsset,destinationInventory)
    if result is not None:
        aUuid,aType = result
        makeItemXml(f.stem,aUuid,aType,destinationInventory)

def copyAndRename(f,destinationAsset,destinationInventory):
    assetType  = ""
    assetUuid  = str(uuid4())
    filename   = str((f.stem))
    extention  = str((f.suffix)).lower()

    match extention:
        case '.lsl':
            assetType = "script"
            extention  = "_" + assetType + extention
        case '.bvh':
            assetType = "animation"
            extention  = "_" + assetType + extention
        case '.tga' | '.jpg' | '.jp2':
            assetType = "texture"
            extention  = "_"  + assetType + extention
        case '.txt' | '.md':
            assetType = "notecard"
            extention  = "_"  + assetType + ".txt"
        case _:
            return None

    destinationFilename = assetUuid + extention
    copy(f,destinationAsset + "/" + destinationFilename)

    match assetType:
        case 'script':
            return [assetUuid,"10"]
        case 'animation':
            return [assetUuid,"20"]
        case 'texture':
            return [assetUuid,"0"]
        case 'notecard':
            return [assetUuid,"7"]

def createArchiveXml(destinationPath):
    archiveXml = Path(str(destinationPath)+'/archive.xml')
    content = """<?xml version="1.0" encoding="utf-16"?>
<archive major_version="0" minor_version="3">
    <assets_included>True</assets_included>
</archive>
"""
    if not archiveXml.exists():
        archiveXml.touch()
        archiveXml.write_text(content)

def makeItemXml(f,aUuid,aType,destination):
    xml = """<?xml version="1.0" encoding="utf-16"?>
<InventoryItem>
    <Name>{name}</Name>
    <ID>{uuid}</ID>
    <InvType>{inventoryType}</InvType>
    <CreatorUUID>00000000-0000-0000-0000-000000000000</CreatorUUID>
    <CreationDate>{creationDate}</CreationDate>
    <Owner>00000000-0000-0000-0000-000000000000</Owner>
    <Description />
    <AssetType>{assetType}</AssetType>
    <AssetID>{assetUuid}</AssetID>
    <SaleType>0</SaleType>
    <SalePrice>0</SalePrice>
    <BasePermissions>581639</BasePermissions>
    <CurrentPermissions>581647</CurrentPermissions>
    <EveryOnePermissions>0</EveryOnePermissions>
    <NextPermissions>2147483647</NextPermissions>
    <Flags>0</Flags>
    <GroupID>00000000-0000-0000-0000-000000000000</GroupID>
    <GroupOwned>False</GroupOwned>
</InventoryItem>
""".format(name=f,uuid=str(uuid4()),inventoryType=aType,creationDate=str(int(datetime.today().timestamp())),assetType=aType,assetUuid=aUuid)
    item = Path(str(destination) + "/" + f + "__" + str(aUuid) + ".xml")
    item.write_text(xml)

def makeIar(destinationPath):
    destination = destinationPath.resolve().parents[0]
    iarPath = Path(argv[2])
    with tarfile.open(name=str(iarPath)+'.iar',mode='x:gz') as tar:
        tar.add(Path(str(iarPath)+'/archive.xml'),arcname=str(Path(str(iarPath)+'/archive.xml').relative_to(iarPath)))
        tar.add(Path(str(iarPath)+'/inventory'),arcname=str(Path(str(iarPath)+'/inventory').relative_to(iarPath)))
        tar.add(Path(str(iarPath)+'/assets'),arcname=str(Path(str(iarPath)+'/assets').relative_to(iarPath)))

##############################################################
######################## Script Begin ########################
##############################################################

if not len(argv) == 3:
    print("Make sure that both source and target paths are provided")
    exit()

sourcePath      = Path(argv[1])
destinationPath = Path(argv[2])

if (type(sourcePath) != type(destinationPath)):
    print("Non conformal paths")
    exit()

if sourcePath.is_dir():
    if not destinationPath.exists():
        Path.mkdir(destinationPath)
    if destinationPath.is_dir():
        createArchiveXml(destinationPath)
        dest = Path(str(destinationPath)+'/assets')
        if not dest.exists():
            dest.mkdir()
        dest = Path(str(destinationPath)+'/inventory')
        if not dest.exists():
            dest.mkdir()
    destinationPath = Path(argv[2]+'/inventory')
    makeIarStructure(sourcePath,destinationPath,addFile)
    makeIar(destinationPath)
else:
    print("Source path is not a directory")
    exit()
