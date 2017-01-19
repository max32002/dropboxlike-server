#!/usr/bin/env python
#encoding=utf-8
import os
from app.dropboxlike import MaxDropboxLikeWeb

if __name__ == "__main__":
#        (r'/', 'controller.HelloHandler'),
    routes = [
        (r'/server_info', 'app.controller.VersionHandler'),
        (r'/1/auth/token', 'app.controller.AuthHandler'),
        (r'/1/repo/claim_auth', 'app.controller.RepoClaimAuthHandler'),
        (r'/1/files_put(.*)', 'app.controller.FilesHandler'),
        (r'/1/files(.*)', 'app.controller.FilesHandler'),
        (r'/1/chunked_upload(.*)', 'app.controller.ChunkUploadHandler'),
        (r'/1/commit_chunked_upload(.*)', 'app.controller.CommitUploadHandler'),
        (r'/1/account/info', 'app.controller.AccountInfoHandler'),
        (r'/1/delta', 'app.controller.DeltaHandler'),
        (r'/1/delta/latest_cursor', 'app.controller.CursorHandler'),
        (r'/1/longpoll_delta', 'app.controller.DeltaHandler'),
        (r'/1/metadata(.*)', 'app.controller.MetaHandler'),
        (r'/1/favorite(.*)', 'app.controller.FavoriteHandler'),
        (r'/1/fileops/copy', 'app.controller.FileCopyHandler'),
        (r'/1/fileops/create_folder', 'app.controller.FileCreateFolderHandler'),
        (r'/1/fileops/delete', 'app.controller.FileDeleteHandler'),
        (r'/1/fileops/move', 'app.controller.FileMoveHandler'),
        (r'/1/fileops/permanently_delete', 'app.controller.FileDeleteHandler'),
        ]

    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__) , 'templates'))
    server = MaxDropboxLikeWeb(routes,template_path)
    
    server.run()
