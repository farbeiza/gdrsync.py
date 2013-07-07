import driveutils
import requestexecutor
import utils

import apiclient.http
import io
import json
import mimetypes
import shutil
import time
import os

def _openSourceFile(sourceFile, targetFile):
    return io.open(sourceFile.path, "rb")

def _openTargetFile(sourceFile, targetFile):
    if targetFile.exists:
        mode = "r+b"
    else:
        mode = "wb"
    output = io.open(targetFile.path, mode)
    output.seek(0)
    return output

def _metadata(sourceFile):
    return json.dumps(sourceFile.metadata(withMd5 = True))

def _copyRemoteFile(context, sourceFile, targetFile):
    if targetFile.exists:
        trashFile(context, targetFile)
    body = sourceFile.delegate.copy()
    body['parents'] = targetFile.delegate['parents']
    file = context.addToBatchAndExecute(context.drive.files().copy(
        fileId = sourceFile.delegate['id'],
        body = body,
        fields = driveutils.FIELDS))
    return targetFile.withDelegate(file)

def _uploadLocalFile(context, sourceFile, targetFile):
    body = targetFile.delegate.copy()
    body['description'] = _metadata(sourceFile)

    (mimeType, _) = mimetypes.guess_type(sourceFile.path)
    if mimeType is None:
        mimeType = utils.DEFAULT_MIME_TYPE

    resumable = (sourceFile.size > utils.CHUNKSIZE)
    if sourceFile.link:
        media = None
    else:
        input =_openSourceFile(sourceFile, targetFile)
        media = apiclient.http.MediaIoBaseUpload(
            input,
            mimetype = mimeType,
            chunksize = utils.CHUNKSIZE,
            resumable = resumable)

    def request():
        if targetFile.exists:
            request = context.drive.files().update(
                fileId = targetFile.delegate['id'],
                body = body,
                media_body = media,
                fields = driveutils.FIELDS)
        else:
            request = context.drive.files().insert(
                body = body,
                media_body = media,
                fields = driveutils.FIELDS)

        start = time.time()
        if not resumable:
            file = request.execute()
            context.logProgress(targetFile.path, start, sourceFile.size)

            return file

        while True:
            (progress, file) = request.next_chunk()
            if file is not None:
                context.logProgress(
                    targetFile.path, start, sourceFile.size)

                return file

            context.logProgress(targetFile.path, start,
                    progress.resumable_progress, progress.total_size,
                    progress.progress(), False)

    file = requestexecutor.execute(request)

    return targetFile.withDelegate(file)

def _downloadRemoteFile(context, sourceFile, targetFile):

    if sourceFile.link:
        os.symlink(sourceFile.metadata()['target'], targetFile.path)
        return targetFile

    def request():
        with _openTargetFile(sourceFile, targetFile) as targetFd:
            http_request = apiclient.http.HttpRequest(
                context.http,
                None,
                sourceFile.delegate.get('downloadUrl'),
                headers = {})
            downloader = apiclient.http.MediaIoBaseDownload(
                targetFd,
                http_request,
                chunksize=utils.CHUNKSIZE)

            start = time.time()
            while True:
                (progress, done) = downloader.next_chunk()
                if done is not None:
                    context.logProgress(targetFile.path, start, sourceFile.size)
		    # If the download is a success, truncate the local file in
		    # case it was longer than the downloaded file.
                    targetFd.truncate()
                    return done

            context.logProgress(targetFile.path, start,
                    progress.resumable_progress, progress.total_size,
                    progress.progress(), False)

    requestexecutor.execute(request)
    return touchFile(context, sourceFile, targetFile)

def _copyLocalFile(context, sourceFile, targetFile):
    if sourceFile.link:
        os.symlink(sourceFile.metadata()['target'], targetFile.path)
        return targetFile

    with io.open(sourceFile.path, "rb") as sourceFd, \
            io.open(targetFile.path, "wb") as targetFd:
        shutil.copyfileobj(sourceFd, targetFd)

    return touchFile(context, sourceFile, targetFile)

def _trashLocalFile(context, targetFile):
    if targetFile.folder:
        shutil.rmtree(targetFile.path)
    else:
        os.unlink(targetFile.path)

def _trashRemoteFile(context, targetFile):
    context.addToBatch(context.drive.files().trash(
        fileId = targetFile.delegate['id'],
        fields = driveutils.FIELDS))

def _touchLocalFile(context, sourceFile, targetFile):
    metadata = sourceFile.metadata()
    os.lchown(targetFile.path,
              metadata.get('uid', -1),
              metadata.get('gid', -1))
    if sourceFile.link:
        if hasattr(os, 'lchmod'):
            os.lchmod(targetFile.path, 0777)
    elif metadata.get('mode'):
        os.chmod(targetFile.path, metadata.get('mode'))
    if not sourceFile.link and not sourceFile.folder:
        os.utime(targetFile.path, (sourceFile.modified.seconds,
                                   sourceFile.modified.seconds))

    return targetFile

def _touchRemoteFile(context, sourceFile, targetFile):
    body = {'description': _metadata(sourceFile)}
    context.addToBatch(context.drive.files().patch(
        fileId = targetFile.delegate['id'],
        body = body,
        setModifiedDate = True,
        fields = driveutils.FIELDS))
    return targetFile

def _insertLocalFolder(context, sourceFile, targetFile):
    os.makedirs(targetFile.path)
    return touchFile(context, sourceFile, targetFile)

def _insertRemoteFolder(context, sourceFile, targetFile):
    body = targetFile.delegate.copy()
    body['description'] = _metadata(sourceFile)
    file = context.addToBatchAndExecute(context.drive.files().insert(
        body = body,
        fields = driveutils.FIELDS))
    return targetFile.withDelegate(file)

def trashFile(context, targetFile):
    return targetFile.select((_trashLocalFile, _trashRemoteFile))(
        context,
        targetFile)

def transferData(context, sourceFile, targetFile):
    actions = (
        (_copyLocalFile, _uploadLocalFile),
        (_downloadRemoteFile, _copyRemoteFile)
    )

    return targetFile.select(sourceFile.select(actions))(
        context,
        sourceFile,
        targetFile)

def touchFile(context, sourceFile, targetFile):
    return targetFile.select((_touchLocalFile, _touchRemoteFile))(
        context,
        sourceFile,
        targetFile)

def insertFolder(context, sourceFile, targetFile):
    return targetFile.select((_insertLocalFolder, _insertRemoteFolder))(
        context,
        sourceFile,
        targetFile)
