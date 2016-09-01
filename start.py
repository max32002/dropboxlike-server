#!/usr/bin/env python
#encoding=utf-8
import os

from maxdropboxlike import MaxDropboxLikeWeb

if __name__ == "__main__":
#        (r'/', 'controller.HelloHandler'),
    routes = [
        (r'/', 'controller.WebSocketHandler'),
        (r'/auth/token', 'controller.AuthHandler'),
        (r'/fileop/v1/files_put(.*)', 'controller.FilesHandler'),
        (r'/fileop/v1/files(.*)', 'controller.FilesHandler'),
        (r'/fileop/v1/chunked_upload(.*)', 'controller.ChunkUploadHandler'),
        (r'/fileop/v1/commit_chunked_upload(.*)', 'controller.CommitUploadHandler'),
        (r'/fileop/v1/usage', 'controller.UsageHandler'),
        (r'/fileop/v1/cursor', 'controller.CursorHandler'),
        (r'/fileop/v1/delta', 'controller.DeltaHandler'),
        (r'/fileop/v1/metadata(.*)', 'controller.MetaHandler'),
        (r'/fileop/v1/favorite(.*)', 'controller.FavoriteHandler'),
        (r'/fileop/v1/fileops/copy', 'controller.FileCopyHandler'),
        (r'/fileop/v1/fileops/create_folder', 'controller.FileCreateFolderHandler'),
        (r'/fileop/v1/fileops/delete', 'controller.FileDeleteHandler'),
        (r'/fileop/v1/fileops/move', 'controller.FileMoveHandler'),
        (r'/ws', 'controller.WebSocketHandler'),

        ]

    template_path = os.path.abspath(__file__ + '/../templates')
    server = MaxDropboxLikeWeb(routes,template_path)
    server.run()
