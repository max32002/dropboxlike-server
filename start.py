#!/usr/bin/env python
#encoding=utf-8
import os

from maxdropboxlike import MaxDropboxLikeWeb

if __name__ == "__main__":
#        (r'/', 'controller.HelloHandler'),
    routes = [
        (r'/version', 'controller.VersionHandler'),
        (r'/1/auth/token', 'controller.AuthHandler'),
        (r'/1/files_put(.*)', 'controller.FilesHandler'),
        (r'/1/files(.*)', 'controller.FilesHandler'),
        (r'/1/chunked_upload(.*)', 'controller.ChunkUploadHandler'),
        (r'/1/commit_chunked_upload(.*)', 'controller.CommitUploadHandler'),
        (r'/1/account/info', 'controller.AccountInfoHandler'),
        (r'/1/delta', 'controller.DeltaHandler'),
        (r'/1/delta/latest_cursor', 'controller.CursorHandler'),
        (r'/1/longpoll_delta', 'controller.DeltaHandler'),
        (r'/1/metadata(.*)', 'controller.MetaHandler'),
        (r'/1/favorite(.*)', 'controller.FavoriteHandler'),
        (r'/1/fileops/copy', 'controller.FileCopyHandler'),
        (r'/1/fileops/create_folder', 'controller.FileCreateFolderHandler'),
        (r'/1/fileops/delete', 'controller.FileDeleteHandler'),
        (r'/1/fileops/move', 'controller.FileMoveHandler'),
        (r'/1/fileops/permanently_delete', 'controller.FileDeleteHandler'),
        ]

    template_path = os.path.abspath(__file__ + '/../templates')
    server = MaxDropboxLikeWeb(routes,template_path)
    server.run()
