## -*- mode: python; coding: utf-8; -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Guest user sessions garbage collector.
"""

__revision__ = "$Id$"

import sys
try:
    from invenio.dbquery import run_sql
    from invenio.config import logdir, tmpdir
    from invenio.bibtask import BibTask, write_message, write_messages
    import time
    import os
except ImportError, e:
    print "Error: %s" % (e, )
    sys.exit(1)

# configure variables
CFG_MYSQL_ARGUMENTLIST_SIZE = 100
# After how many days to remove obsolete log/err files
CFG_MAX_ATIME_RM_LOG = 28
# After how many days to zip obsolete log/err files
CFG_MAX_ATIME_ZIP_LOG = 7
# After how many days to remove obsolete bibreformat fmt xml files
CFG_MAX_ATIME_RM_FMT = 28
# After how many days to zip obsolete bibreformat fmt xml files
CFG_MAX_ATIME_ZIP_FMT = 7
# After how many days to remove obsolete bibharvest fmt xml files
CFG_MAX_ATIME_RM_OAI = 28
# After how many days to zip obsolete bibharvest fmt xml files
CFG_MAX_ATIME_ZIP_OAI = 7

def gc_exec_command(command, verbose=1):
    """ Exec the command logging in appropriate way its output."""
    if verbose >= 9:
        write_message('  %s' % command)
    (dontcare, output, errors) = os.popen3(command)
    write_messages(errors.read())
    if verbose: write_messages(output.read())

def clean_filesystem(verbose=1):
    """ Clean the filesystem from obsolete files. """
    if verbose: write_message("""FILESYSTEM CLEANING STARTED""")
    if verbose: write_message("- deleting/gzipping bibsched empty/old err/log "
            "BibSched files")
    vstr = verbose > 1 and '-v' or ''
    gc_exec_command('find %s -name "bibsched_task_*"'
        ' -size 0c -exec rm %s -f {} \;' \
            % (logdir, vstr), verbose)
    gc_exec_command('find %s -name "bibsched_task_*"'
        ' -atime +%s -exec rm %s -f {} \;' \
            % (logdir, CFG_MAX_ATIME_RM_LOG, vstr), verbose)
    gc_exec_command('find %s -name "bibsched_task_*"'
        ' -atime +%s -exec gzip %s -9 {} \;' \
            % (logdir, CFG_MAX_ATIME_ZIP_LOG, vstr), verbose)

    if verbose: write_message("- deleting/gzipping temporary empty/old "
            "BibReformat xml files")
    gc_exec_command('find %s -name "rec_fmt_*"'
        ' -size 0c -exec rm %s -f {} \;' \
            % (tmpdir, vstr), verbose)
    gc_exec_command('find %s -name "rec_fmt_*"'
        ' -atime +%s -exec rm %s -f {} \;' \
            % (tmpdir, CFG_MAX_ATIME_RM_FMT, vstr), verbose)
    gc_exec_command('find %s -name "rec_fmt_*"'
        ' -atime +%s -exec gzip %s -9 {} \;' \
            % (tmpdir, CFG_MAX_ATIME_ZIP_FMT, vstr), verbose)

    if verbose: write_message("- deleting/gzipping temporary old "
            "BibHarvest xml files")
    gc_exec_command('find %s -name "bibharvestadmin.*"'
        ' -exec rm %s -f {} \;' \
            % (tmpdir, vstr), verbose)
    gc_exec_command('find %s -name "bibconvertrun.*"'
        ' -exec rm %s -f {} \;' \
            % (tmpdir, vstr), verbose)
    gc_exec_command('find %s -name "oaiharvest*"'
        ' -atime +%s -exec gzip %s -9 {} \;' \
            % (tmpdir, CFG_MAX_ATIME_ZIP_OAI, vstr), verbose)
    gc_exec_command('find %s -name "oaiharvest*"'
        ' -atime +%s -exec rm %s -f {} \;' \
            % (tmpdir, CFG_MAX_ATIME_RM_OAI, vstr), verbose)
    gc_exec_command('find %s -name "oai_archive*"'
        ' -atime +%s -exec rm %s -f {} \;' \
            % (tmpdir, CFG_MAX_ATIME_RM_OAI, vstr), verbose)
    if verbose: write_message("""FILESYSTEM CLEANING FINISHED""")


def guest_user_garbage_collector(verbose=1):
    """Session Garbage Collector

    program flow/tasks:
    1: delete expired sessions
    1b:delete guest users without session
    2: delete queries not attached to any user
    3: delete baskets not attached to any user
    4: delete alerts not attached to any user

    verbose - level of program output.
              0 - nothing
              1 - default
              9 - max, debug"""

    # dictionary used to keep track of number of deleted entries
    delcount = {'session': 0,
                'user': 0,
                'user_query': 0,
                'query': 0,
                'bskBASKET': 0,
                'user_bskBASKET': 0,
                'bskREC': 0,
                'bskRECORDCOMMENT':0,
                'bskEXTREC':0,
                'bskEXTFMT':0,
                'user_query_basket': 0}

    if verbose: write_message("GUEST USER SESSIONS GARBAGE"
        " COLLECTOR STARTED")

    # 1 - DELETE EXPIRED SESSIONS
    if verbose: write_message("- deleting expired sessions")
    timelimit = time.time()
    if verbose >= 9: write_message("  DELETE FROM session WHERE"
        " session_expiry < %d \n" % (timelimit, ))
    delcount['session'] += run_sql("DELETE FROM session WHERE"
        " session_expiry < %s """ % (timelimit, ))


    # 1b - DELETE GUEST USERS WITHOUT SESSION
    if verbose: write_message("- deleting guest users without session")

    # get uids
    if verbose >= 9: write_message("""  SELECT u.id\n  FROM user AS u LEFT JOIN session AS s\n  ON u.id = s.uid\n  WHERE s.uid IS NULL AND u.email = ''""")

    result = run_sql("""SELECT u.id
    FROM user AS u LEFT JOIN session AS s
    ON u.id = s.uid
    WHERE s.uid IS NULL AND u.email = ''""")
    if verbose >= 9: write_message(result)

    if result:
        # work on slices of result list in case of big result
        for i in range(0, len(result), CFG_MYSQL_ARGUMENTLIST_SIZE):
            # create string of uids
            uidstr = ''
            for (id_user, ) in result[i:i+CFG_MYSQL_ARGUMENTLIST_SIZE]:
                if uidstr: uidstr += ','
                uidstr += "%s" % (id_user, )

            # delete users
            if verbose >= 9: write_message("  DELETE FROM user WHERE"
                " id IN (TRAVERSE LAST RESULT) AND email = '' \n")
            delcount['user'] += run_sql("DELETE FROM user WHERE"
                " id IN (%s) AND email = ''" % (uidstr, ))


    # 2 - DELETE QUERIES NOT ATTACHED TO ANY USER

    # first step, delete from user_query
    if verbose: write_message("- deleting user_queries referencing"
        " non-existent users")

    # find user_queries referencing non-existent users
    if verbose >= 9: write_message("  SELECT DISTINCT uq.id_user\n"
        "  FROM user_query AS uq LEFT JOIN user AS u\n"
        "  ON uq.id_user = u.id\n  WHERE u.id IS NULL")
    result = run_sql("""SELECT DISTINCT uq.id_user
        FROM user_query AS uq LEFT JOIN user AS u
        ON uq.id_user = u.id
        WHERE u.id IS NULL""")
    if verbose >= 9: write_message(result)


    # delete in user_query one by one
    if verbose >= 9: write_message("  DELETE FROM user_query WHERE"
        " id_user = 'TRAVERSE LAST RESULT' \n")
    for (id_user, ) in result:
        delcount['user_query'] += run_sql("""DELETE FROM user_query
            WHERE id_user = %s""" % (id_user, ))

    # delete the actual queries
    if verbose: write_message("- deleting queries not attached to any user")

    # select queries that must be deleted
    if verbose >= 9: write_message("""  SELECT DISTINCT q.id\n  FROM query AS q LEFT JOIN user_query AS uq\n  ON uq.id_query = q.id\n  WHERE uq.id_query IS NULL AND\n  q.type <> 'p' """)
    result = run_sql("""SELECT DISTINCT q.id
                        FROM query AS q LEFT JOIN user_query AS uq
                        ON uq.id_query = q.id
                        WHERE uq.id_query IS NULL AND
                              q.type <> 'p'""")
    if verbose >= 9: write_message(result)

    # delete queries one by one
    if verbose >= 9: write_message("""  DELETE FROM query WHERE id = 'TRAVERSE LAST RESULT \n""")
    for (id_user, ) in result:
        delcount['query'] += run_sql("""DELETE FROM query WHERE id = %s""" % (id_user, ))


    # 3 - DELETE BASKETS NOT OWNED BY ANY USER
    if verbose: write_message("- deleting baskets not owned by any user")

    # select basket ids
    if verbose >= 9: write_message(""" SELECT ub.id_bskBASKET\n  FROM user_bskBASKET AS ub LEFT JOIN user AS u\n  ON u.id = ub.id_user\n  WHERE u.id IS NULL""")
    try:
        result = run_sql("""SELECT ub.id_bskBASKET
                              FROM user_bskBASKET AS ub LEFT JOIN user AS u
                                ON u.id = ub.id_user
                             WHERE u.id IS NULL""")
    except:
        result = []
    if verbose >= 9: write_message(result)

    # delete from user_basket and basket one by one
    if verbose >= 9:
        write_message("""  DELETE FROM user_bskBASKET WHERE id_bskBASKET = 'TRAVERSE LAST RESULT' """)
        write_message("""  DELETE FROM bskBASKET WHERE id = 'TRAVERSE LAST RESULT' """)
        write_message("""  DELETE FROM bskREC WHERE id_bskBASKET = 'TRAVERSE LAST RESULT'""")
        write_message("""  DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET = 'TRAVERSE LAST RESULT' \n""")
    for (id_basket, ) in result:
        delcount['user_bskBASKET'] += run_sql("""DELETE FROM user_bskBASKET WHERE id_bskBASKET = %s""" % (id_basket, ))
        delcount['bskBASKET'] += run_sql("""DELETE FROM bskBASKET WHERE id = %s""" % (id_basket, ))
        delcount['bskREC'] += run_sql("""DELETE FROM bskREC WHERE id_bskBASKET = %s""" % (id_basket, ))
        delcount['bskRECORDCOMMENT'] += run_sql("""DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET = %s""" % (id_basket, ))
    if verbose >= 9: write_message(""" SELECT DISTINCT ext.id, rec.id_bibrec_or_bskEXTREC FROM bskEXTREC AS ext \nLEFT JOIN bskREC AS rec ON ext.id=-rec.id_bibrec_or_bskEXTREC WHERE id_bibrec_or_bskEXTREC is NULL""")
    try:
        result = run_sql("""SELECT DISTINCT ext.id FROM bskEXTREC AS ext
                            LEFT JOIN bskREC AS rec ON ext.id=-rec.id_bibrec_or_bskEXTREC
                            WHERE id_bibrec_or_bskEXTREC is NULL""")
    except:
        result = []
    if verbose >= 9:
        write_message(result)
        write_message("""  DELETE FROM bskEXTREC WHERE id = 'TRAVERSE LAST RESULT' """)
        write_message("""  DELETE FROM bskEXTFMT WHERE id_bskEXTREC = 'TRAVERSE LAST RESULT' \n""")
    for (id_basket, ) in result:
        delcount['bskEXTREC'] += run_sql("""DELETE FROM bskEXTREC WHERE id=%s""" % (id_basket,))
        delcount['bskEXTFMT'] += run_sql("""DELETE FROM bskEXTFMT WHERE id_bskEXTREC=%s""" % (id_basket,))

    # 4 - DELETE ALERTS NOT OWNED BY ANY USER
    if verbose: write_message('- deleting alerts not owned by any user')

    # select user ids in uqb that reference non-existent users
    if verbose >= 9: write_message("""SELECT DISTINCT uqb.id_user FROM user_query_basket AS uqb LEFT JOIN user AS u ON uqb.id_user = u.id WHERE u.id IS NULL""")
    result = run_sql("""SELECT DISTINCT uqb.id_user FROM user_query_basket AS uqb LEFT JOIN user AS u ON uqb.id_user = u.id WHERE u.id IS NULL""")
    if verbose >= 9: write_message(result)

    # delete all these entries
    for (id_user, ) in result:
        if verbose >= 9: write_message("""DELETE FROM user_query_basket WHERE id_user = 'TRAVERSE LAST RESULT """)
        delcount['user_query_basket'] += run_sql("""DELETE FROM user_query_basket WHERE id_user = %s """ % (id_user, ))


    # print STATISTICS

    if verbose:
        write_message("""STATISTICS - DELETED DATA: """)
        write_message("""- %7s sessions.""" % (delcount['session'], ))
        write_message("""- %7s users.""" % (delcount['user'], ))
        write_message("""- %7s user_queries.""" % (delcount['user_query'], ))
        write_message("""- %7s queries.""" % (delcount['query'], ))
        write_message("""- %7s baskets.""" % (delcount['bskBASKET'], ))
        write_message("""- %7s user_baskets.""" % (delcount['user_bskBASKET'], ))
        write_message("""- %7s basket_records.""" % (delcount['bskREC'], ))
        write_message("""- %7s basket_external_records.""" % (delcount['bskEXTREC'], ))
        write_message("""- %7s basket_external_formats.""" % (delcount['bskEXTFMT'], ))
        write_message("""- %7s basket_comments.""" % (delcount['bskRECORDCOMMENT'], ))
        write_message("""- %7s user_query_baskets.""" % (delcount['user_query_basket'], ))
        write_message("""GUEST USER SESSIONS GARBAGE COLLECTOR FINISHED""")

    return


def test_insertdata():
    """insert testdata for the garbage collector.
    something will be deleted, other data kept.
    test_checkdata() checks if the remains are correct."""

    test_deletedata_nooutput()

    print 'insert into session 6'
    for (key, uid) in [('23A', 2000), ('24B', 2100), ('25C', 2200), ('26D', 2300)]:
        run_sql("""INSERT INTO session (session_key, session_expiry, uid) values ('%s', %d, %s) """ % (key, time.time(), uid))
    for (key, uid) in [('27E', 2400), ('28F', 2500)]:
        run_sql("""INSERT INTO session (session_key, session_expiry, uid) values ('%s', %d, %s) """ % (key, time.time()+20000, uid))

    print 'insert into user 6'
    for id in range(2000, 2600, 100):
        run_sql("""INSERT INTO user (id, email) values (%s, '') """ % (id, ))

    print 'insert into user_query 6'
    for (id_user, id_query) in [(2000, 155), (2100, 231), (2200, 155), (2300, 574), (2400, 155), (2500, 988)]:
        run_sql("""INSERT INTO user_query (id_user, id_query) values (%s, %s) """ % (id_user, id_query))

    print 'insert into query 4'
    for (id, urlargs) in [(155, 'p=cern'), (231, 'p=muon'), (574, 'p=physics'), (988, 'cc=Atlantis+Institute+of+Science&as=0&p=')]:
        run_sql("""INSERT INTO query (id, type, urlargs) values (%s, 'r', '%s') """ % (id, urlargs))

    print 'insert into basket 4'
    for (id, name) in [(6, 'general'), (7, 'physics'), (8, 'cern'), (9, 'diverse')]:
        run_sql("""INSERT INTO basket (id, name, public) values (%s, '%s', 'n')""" % (id, name))

    print 'insert into user_basket 4'
    for (id_user, id_basket) in [(2000, 6), (2200, 7), (2200, 8), (2500, 9)]:
        run_sql("""INSERT INTO user_basket (id_user, id_basket) values (%s, %s) """ % (id_user, id_basket))

    print 'insert into user_query_basket 2'
    for (id_user, id_query, id_basket) in [(2200, 155, 6), (2500, 988, 9)]:
        run_sql("""INSERT INTO user_query_basket (id_user, id_query, id_basket) values (%s, %s, %s) """ % (id_user, id_query, id_basket))

def test_deletedata():
    """deletes all the testdata inserted in the insert function.
    outputs how many entries are deleted"""

    print 'delete from session',
    print run_sql("DELETE FROM session WHERE uid IN (2000,2100,2200,2300,2400,2500) ")
    print 'delete from user',
    print run_sql("DELETE FROM user WHERE id IN (2000,2100,2200,2300,2400,2500) ")
    print 'delete from user_query',
    print run_sql("DELETE FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) OR id_query IN (155,231,574,988) ")
    print 'delete from query',
    print run_sql("DELETE FROM query WHERE id IN (155,231,574,988) ")
    print 'delete from basket',
    print run_sql("DELETE FROM basket WHERE id IN (6,7,8,9) ")
    print 'delete from user_basket',
    print run_sql("DELETE FROM user_basket WHERE id_basket IN (6,7,8,9) OR id_user IN (2000, 2200, 2500) ")
    print 'delete from user_query_basket',
    print run_sql("DELETE FROM user_query_basket WHERE id_user IN (2200, 2500) ")


def test_deletedata_nooutput():
    """same as test_deletedata without output."""

    run_sql("DELETE FROM session WHERE uid IN (2000,2100,2200,2300,2400,2500) ")
    run_sql("DELETE FROM user WHERE id IN (2000,2100,2200,2300,2400,2500) ")
    run_sql("DELETE FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) OR id_query IN (155,231,574,988) ")
    run_sql("DELETE FROM query WHERE id IN (155,231,574,988) ")
    run_sql("DELETE FROM basket WHERE id IN (6,7,8,9) ")
    run_sql("DELETE FROM user_basket WHERE id_basket IN (6,7,8,9) OR id_user IN (2000, 2200, 2500) ")
    run_sql("DELETE FROM user_query_basket WHERE id_user IN (2200, 2500) ")


def test_showdata():
    print '\nshow test data:'

    print '\n- select * from session:'
    for r in run_sql("SELECT * FROM session WHERE session_key IN ('23A','24B','25C','26D','27E','28F') "): print r

    print '\n- select * from user:'
    for r in run_sql("SELECT * FROM user WHERE email = '' AND id IN (2000,2100,2200,2300,2400,2500) "): print r

    print '\n- select * from user_query:'
    for r in run_sql("SELECT * FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) "): print r

    print '\n- select * from query:'
    for r in run_sql("SELECT * FROM query  WHERE id IN (155,231,574,988) "): print r

    print '\n- select * from basket:'
    for r in run_sql("SELECT * FROM basket WHERE id IN (6,7,8,9) "): print r

    print '\n- select * from user_basket:'
    for r in run_sql("SELECT * FROM user_basket WHERE id_basket IN (6,7,8,9)"): print r

    print '\n- select * from user_query_basket:'
    for r in run_sql("SELECT * FROM user_query_basket WHERE id_basket IN (6,7,8,9) "): print r


def test_checkdata():
    """checks wether the data in the database is correct after
    the garbage collector has run.
    test_insertdata must have been run followed by the gc for this to be true."""

    result = run_sql("SELECT DISTINCT session_key"
        " FROM session WHERE session_key"
        " IN ('23A','24B','25C','26D','27E','28F') ")
    if len(result) != 2: return 0
    for r in [('27E', ), ('28F', )]:
        if r not in result: return 0

    result = run_sql("SELECT id FROM user WHERE email = '' AND id IN (2000,2100,2200,2300,2400,2500) ")
    if len(result) != 2: return 0
    for r in [(2400, ), (2500, )]:
        if r not in result: return 0

    result = run_sql("SELECT DISTINCT id_user FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) ")
    if len(result) != 2: return 0
    for r in [(2400, ), (2500, )]:
        if r not in result: return 0

    result = run_sql("SELECT id FROM query  WHERE id IN (155,231,574,988) ")
    if len(result) != 2: return 0
    for r in [(155, ), (988, )]:
        if r not in result: return 0

    result = run_sql("SELECT id FROM basket WHERE id IN (6,7,8,9) ")
    if len(result) != 1: return 0
    for r in [(9, )]:
        if r not in result: return 0

    result = run_sql("SELECT id_user, id_basket"
        " FROM user_basket WHERE id_basket IN (6,7,8,9)")
    if len(result) != 1: return 0
    for r in [(2500, 9)]:
        if r not in result: return 0

    result = run_sql("SELECT id_user, id_query, id_basket"
        " FROM user_query_basket WHERE id_basket IN (6,7,8,9) ")
    if len(result) != 1: return 0
    for r in [(2500, 988, 9)]:
        if r not in result: return 0

    return 1

def test_runtest_guest_user_garbage_collector():
    """a test to see if the garbage collector works correctly."""

    test_insertdata()
    test_showdata()
    guest_user_garbage_collector(verbose=9)
    test_showdata()
    if test_checkdata():
        print '\n\nGARBAGE COLLECTOR CLEANED ' \
            'UP THE CORRECT DATA \n\n'
    else:
        print '\n\nERROR ERROR ERROR - WRONG DATA CLEANED - ' \
            'ERROR ERROR ERROR \n\n'
    test_deletedata_nooutput()
    return

class SessionGCBibTask(BibTask):
    def __init__(self):
        """Construct a SessionGCBibTask"""
        BibTask.__init__(self,
            authorization_msg='SessionGC',
            authorization_action='runsessiongc',
            specific_params=("f", ["filesystem"]),
            help_specific_usage="  -f, --filesystem\t\t Clean up the"
                " filesystem.\n",
            description="Description: %s garbage collects all the"
                " guests users sessions\n" % sys.argv[0])

    def task_submit_elaborate_specific_parameter(self, key, value):
        """ Given the string key it checks it's meaning, eventually using the
        value. Usually it fills some key in the options dict.
        It must return True if it has elaborated the key, False, if it doesn't
        know that key.
        eg:
        if key in ['-n', '--number']:
            self.options['number'] = value
            return True
        return False
        """
        if key in ['-f', '--filesystem']:
            self.options['filesystem'] = True
            return True
        return False

    def task_run_core(self):
        """ Reimplement to add the body of the task."""
        guest_user_garbage_collector(self.options["verbose"])
        if self.options.get("filesystem", False):
            clean_filesystem(self.options["verbose"])

def main():
    """CLI to the session garbage collector."""
    task = SessionGCBibTask()
    task.main()

if __name__ == '__main__':
    main()