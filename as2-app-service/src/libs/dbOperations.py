from sqlalchemy import text
from models.as2 import as2DbHandler
from models.gitleaks import gitleaksScanResultsTable
from models.bitbucketServer import bitbucketServerScanResultsTable

class DBOperations():
    def __init__(self):
        pass

    def auth(self):
        # Execute a db query to verify the connection 
        # Checks DB authentication 
        # Returns 200 -> Success
        #         0 -> Failure 
        from app import app
        with app.app_context():
            try:
                as2DbHandler.session.query(text("1")).from_statement(text("SELECT 1")).all()
                db_status_code = 200
            except Exception as e:
                print('ERROR - authCheck - error: {}'.format(e))
                db_status_code = 0
        return db_status_code

    def selectOneRecord(self, tableName, condition):
        # This function returns a record that contains all columns from a table 
        print('INFO - DBOperations - Execute selectOneRecord function')
        select_sql = text('select * from {} where {}'.format(tableName, condition))
        tableData = as2DbHandler.session.execute(select_sql)
        for t in tableData:
            data = dict(t)
        return data

    def updateRecord(self, tableName, condition, values):
        # This function updates a record in a table 
        print('INFO - DBOperations - Execute updateRecord function')
        try:
            #as2DbHandler.session.execute(update(tableInstatnce).where(condition).values(values['data']))
            update_sql = text('update {} set {} where {}'.format(tableName, values['data'], condition))
            updateData = as2DbHandler.session.execute(update_sql)
            as2DbHandler.session.commit()
            data = {'status': 'success'}
        except Exception as e:
            print('ERROR - updateRecord - Failed to update record # {}'.format(e))
            data = {'status': 'error'}
        return data

    def gitleaksUpsertRecord(self, DbHandler, tableName, values):
        # This function is to insert a record 
        # If exist update the values 
        print('INFO - DBOperations - Execute gitleaksUpsertRecord function')
        from app import app
        with app.app_context():
            try:
                upsert_sql = text('INSERT INTO {tablename} (project, repository, secretscount, updatedat) VALUES {values} ON CONFLICT (project, repository) DO UPDATE SET secretscount = EXCLUDED.secretscount, updatedat = EXCLUDED.updatedat;'.format(tablename=tableName, values=values))
                upsertData = DbHandler.session.execute(upsert_sql)
                DbHandler.session.commit()
                data = {'status': 'success'}
            except Exception as e:
                print('ERROR - gitleaksUpsertRecord - Failed to update record # {}'.format(e))
                data = {'status': 'error'}
        return data

    def bitbucketServerUpsertRecord(self, DbHandler, tableName, values):
        # This function is to insert a record 
        # If exist update the values 
        print('INFO - DBOperations - Execute bitbucketServerUpsertRecord function')
        from app import app
        with app.app_context():
            try:
                upsert_sql = text('INSERT INTO {tablename} (project, repository, lastcommitdate, lastcommitname, lastcommitemail, updatedat) VALUES {values} ON CONFLICT (project, repository) DO UPDATE SET lastcommitdate = EXCLUDED.lastcommitdate, lastcommitname = EXCLUDED.lastcommitname, lastcommitemail = EXCLUDED.lastcommitemail, updatedat = EXCLUDED.updatedat;'.format(tablename=tableName, values=values))
                upsertData = DbHandler.session.execute(upsert_sql)
                DbHandler.session.commit()
                data = {'status': 'success'}
            except Exception as e:
                print('ERROR - bitbucketServerUpsertRecord - Failed to update record # {}'.format(e))
                data = {'status': 'error'}
        return data

    def analysisView(self):
        # This function is to insert a record 
        # If exist update the values 
        print('INFO - DBOperations - Execute analysisViewRecords function')
        select_sql = text("SELECT '' as exp, gl.project, gl.repository, gl.secretscount, bs.lastcommitdate FROM {gitleaks_tablename} gl JOIN {bitbucketserver_tablename} bs ON (gl.project = bs.project and gl.repository = bs.repository);".format(gitleaks_tablename=gitleaksScanResultsTable.__tablename__, bitbucketserver_tablename=bitbucketServerScanResultsTable.__tablename__))
        tableData = as2DbHandler.session.execute(select_sql)
        data = []
        for t in tableData:
            data.append(list(dict(t).values()))
        return data

    def analysisViewRecord(self, project, repository):
        # This function is to insert a record 
        # If exist update the values 
        print('INFO - DBOperations - Execute analysisViewRecords function')
        select_sql = text("SELECT gl.project, gl.repository, gl.secretscount, bs.lastcommitname, bs.lastcommitemail, bs.lastcommitdate FROM {gitleaks_tablename} gl JOIN {bitbucketserver_tablename} bs ON (gl.project = bs.project and gl.repository = bs.repository) WHERE gl.project='{_project}' and gl.repository='{_repository}';".format(gitleaks_tablename=gitleaksScanResultsTable.__tablename__, bitbucketserver_tablename=bitbucketServerScanResultsTable.__tablename__, _project=project, _repository=repository))
        tableData = as2DbHandler.session.execute(select_sql)
        for t in tableData:
            data = dict(t)
        return data