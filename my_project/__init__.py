# Let Django's MySQL backend use PyMySQL (pure-Python) instead of mysqlclient.
# Harmless no-op when running on a non-MySQL backend (e.g. Postgres) or when
# PyMySQL is not installed.
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass