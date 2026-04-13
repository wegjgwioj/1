# coding:utf-8
import click,py_compile,os
from configparser import ConfigParser
from util.configread import config_read
from util.sqlinit import Create
@click.group()
def sub():
    pass


@click.command()
def initdb(ini="config.ini"):
    dbtype, host, port, user, passwd, dbName, charset,_ = config_read(ini)
    if dbtype == 'mysql':
        cm = Create(dbtype, host, port, user, passwd, dbName, charset)
        mysql_charset = charset or "utf8mb4"
        mysql_collation = "utf8mb4_unicode_ci" if mysql_charset == "utf8mb4" else "utf8_general_ci"
        cm.create_db(
            "CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET {} COLLATE {};".format(
                dbName, mysql_charset, mysql_collation
            )
        )

        cm.conn_close()
    elif dbtype == 'mssql':
        cm = Create(dbtype, host, port, user, passwd, dbName, charset)
        cm.create_db("CREATE DATABASE IF NOT EXISTS  `{}` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;".format(dbName))

        cm.conn_close()
    else:
        print('请修改当前面目录下的config.ini文件')

@click.command()
def initsql(ini="config.ini"):
    dbtype, host, port, user, passwd, dbName, charset,_ = config_read(ini)
    if dbtype == 'mysql':
        cm = Create(dbtype, host, port, user, passwd, dbName, charset)
        mysql_charset = charset or "utf8mb4"
        mysql_collation = "utf8mb4_unicode_ci" if mysql_charset == "utf8mb4" else "utf8_general_ci"
        cm.create_db(
            "CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET {} COLLATE {};".format(
                dbName, mysql_charset, mysql_collation
            )
        )
        with open("./db/diandong5k56la1f.sql", encoding="utf8") as f:
            createsql = f.read()
        createsql = "DROP TABLE" + createsql.split('DROP TABLE', 1)[-1]
        cm.create_tables(createsql.split(';\n')[:-1])
        cm.conn_close()
    elif dbtype == 'mssql':
        cm = Create(dbtype, host, port, user, passwd, dbName, charset)
        cm.create_db("CREATE DATABASE IF NOT EXISTS  `{}` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;".format(dbName))
        with open("./db/mssql.sql", encoding="utf8") as f:
            createsql = f.read()
        createsql = "DROP TABLE" + createsql.split('DROP TABLE', 1)[-1]
        cm.create_tables(createsql.split(';\n')[:-1])
        cm.conn_close()
    else:
        print('请修改当前面目录下的config.ini文件')

sub.add_command(initdb,"initdb")
sub.add_command(initsql,"initsql")
if __name__ == "__main__":
    sub()
