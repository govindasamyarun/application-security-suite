import os
from sqlalchemy import select, update, text
from models.gitleaks import gitLeaksDbHandler, gitLeaksEventsTable, gitLeaksSettingsTable

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
                gitLeaksDbHandler.session.query(text("1")).from_statement(text("SELECT 1")).all()
                db_status_code = 200
            except Exception as e:
                print('ERROR - authCheck - error: {}'.format(e))
                db_status_code = 0
        return db_status_code

    def selectOneRecord(self, tableName, condition):
        # This function returns a record that contains all columns from a table 
        print('INFO - DBOperations - Execute selectOneRecord function')
        select_sql = text('select * from {} where {}'.format(tableName, condition))
        tableData = gitLeaksDbHandler.session.execute(select_sql)
        for t in tableData:
            data = dict(t)
        return data

    def updateRecord(self, tableName, condition, values):
        # This function updates a record in a table 
        print('INFO - DBOperations - Execute updateRecord function')
        try:
            #gitLeaksDbHandler.session.execute(update(tableInstatnce).where(condition).values(values['data']))
            update_sql = text('update {} set {} where {}'.format(tableName, values['data'], condition))
            updateData = gitLeaksDbHandler.session.execute(update_sql)
            gitLeaksDbHandler.session.commit()
            data = {'status': 'success'}
        except Exception as e:
            print('ERROR - dbUpdateRecord - Failed to update record # {}'.format(e))
            data = {'status': 'error'}
        return data