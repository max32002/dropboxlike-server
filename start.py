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

        (r'/1/files/list_folder', 'app.controller.ListFolderHandler'),
        (r'/1/files/get_metadata', 'app.controller.MetadataHandler'),
        (r'/1/files/create_folder', 'app.controller.FileCreateFolderHandler'),
        (r'/1/files/delete', 'app.controller.FileDeleteHandler'),
        # [TODO]:
        (r'/1/files/permanently_delete', 'app.controller.FileDeleteHandler'),

        (r'/1/files/copy', 'app.controller.FileCopyHandler'),
        (r'/1/files/move', 'app.controller.FileMoveHandler'),
        (r'/1/files/upload', 'app.controller.UploadHandler'),
        (r'/1/files/upload_session/start', 'app.controller.UploadSessionStartHandler'),
        (r'/1/files/upload_session/append', 'app.controller.UploadSessionAppendHandler'),
        (r'/1/files/upload_session/finish', 'app.controller.UploadSessionFinishHandler'),
        (r'/1/files/download', 'app.controller.DownloadHandler'),
        (r'/1/files/get_thumbnail', 'app.controller.ThumbnailHandler'),

        # share repo
        (r'/1/sharing/create_shared_repo', 'app.controller.RepoShareCreateHandler'),
        (r'/1/repo/auth_shared_repo', 'app.controller.RepoShareAuthHandler'),
        # share folder
        (r'/1/sharing/create_shared_folder', 'app.controller.RepoShareCreateHandler'),
        (r'/1/repo/auth_shared_folder', 'app.controller.RepoShareAuthHandler'),

        # [TODO]: for streaming
        (r'/1/files/get_temporary_link', 'app.controller.MetadataHandler'),

        # merge to /1/files/list_folder with new parament.
        #(r'/1/delta', 'app.controller.DeltaHandler'),
        (r'/1/list_folder/longpoll', 'app.controller.DeltaHandler'),
        (r'/1/list_folder/get_latest_cursor', 'app.controller.CursorHandler'),
        
        (r'/1/users/get_space_usage', 'app.controller.AccountUsageHandler'),
        (r'/1/users/security_question', 'app.controller.AccountSecurityQuestionHandler'),
        # [TODO]:
        #(r'/1/favorite', 'app.controller.FavoriteHandler'),
        ]

    routes_http = [
        (r'/server_info', 'app.controller.VersionHandler'),
        ]
    server = MaxDropboxLikeWeb(routes, routes_http)
    
    server.run()
