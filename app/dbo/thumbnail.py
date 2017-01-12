import logging
from dbo.basetable import BaseTable

#data object for Account
#############################################################
class DboThumbnail(BaseTable):
    sql_return_fields = "id"
    sql_table_name = "thumbnail"
    sql_primary_key = "id"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `thumbnail` (
  `id`  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
);
    '''
