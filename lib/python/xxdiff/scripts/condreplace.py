#!/usr/bin/env python
#******************************************************************************\
#* Copyright (C) 2003-2006 Martin Blais <blais@furius.ca>
#*
#* This program is free software; you can redistribute it and/or modify
#* it under the terms of the GNU General Public License as published by
#* the Free Software Foundation; either version 2 of the License, or
#* (at your option) any later version.
#*
#* This program is distributed in the hope that it will be useful,
#* but WITHOUT ANY WARRANTY; without even the implied warranty of
#* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#* GNU General Public License for more details.
#*
#* You should have received a copy of the GNU General Public License
#* along with this program; if not, write to the Free Software
#* Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#*
#*****************************************************************************/

"""xxdiff-cond-replace [<options>] <orig-file> <modified-file>

Useful script to conditionally replace a original by a generated file.

Basically, you invoke some script or pipeline of scripts to perform
modifications on an original text file and store the results in a temporary file
(the modified-file), and then invoke this script to conditionally overwrite the
contents of the orig-file with those of the modified file.

This works like copy (``cp``), except that xxdiff is shown to ask the user
whether to copy the file or not.  This is useful to run in a loop, for example::

   for i in `*/*.xml` ; do
      cat $i | ...pipeline of cmds that modifies the file... > /tmp/out.xml
      # copy only if the user accepts or merges.
      xxdiff-cond-replace $i /tmp/out.xml
   done

**IMPORTANT**: Notice well that the original file which will be overwritten is
on the LEFT side. The syntax is the reverse of the UNIX cp command.

Exit Status
-----------

This program exits with status 0 if the copy operation was accepted or merged,
with 1 otherwise.

Notes
-----

- the script automatically creates backup files.
- the script automatically generates a detailed log of its actions and
  a text summary of all the differences beteween the original and new files.
- the script can optionally checkout the file with ClearCase before performing
  the replacement.

"""

__version__ = "$Revision: 857 $"
__author__ = "Martin Blais <blais@furius.ca>"
__depends__ = ['xxdiff', 'Python-2.3']
__copyright__ = """Copyright (C) 2003-2004 Martin Blais <blais@furius.ca>.
This code is distributed under the terms of the GNU General Public License."""


# stdlib imports.
import sys, os, re
from os.path import *
import commands, tempfile, shutil


tmpprefix = '%s.' % basename(sys.argv[0])

#-------------------------------------------------------------------------------
#
def backup( fn, opts ):
    """
    Compute backup filename and copy backup file.
    """

    if opts.backup_type == 'parallel':
        fmt = '%s.bak.%d'
        ii = 0
        while 1:
            backupfn = fmt % (fn, ii)
            if not exists(backupfn):
                break
            ii += 1

    elif opts.backup_type == 'other':
        ##afn = abspath(fn)
        backupfn = normpath(join(opts.backup_dir, fn))
    else:
        backupfn = None

    if backupfn:
        if not opts.silent:
            print 'Backup:', backupfn
        ddn = dirname(backupfn)
        if ddn and not exists(ddn):
            os.makedirs(ddn)
        shutil.copy2(fn, backupfn)

#-------------------------------------------------------------------------------
#
def cc_checkout(fn, opts):
    """
    Checkout the file from ClearCase.
    """
    if not opts.silent:
        print 'Checking out the file'
    os.system('cleartool co -nc "%s"' % fn)

#-------------------------------------------------------------------------------
#
def cond_replace( origfile, modfile, opts ):
    """
    Spawn xxdiff and perform the replacement if confirmed.
    """

    if opts.diff:
        print '=' * 80
        print 'File:    ', origfile
        print 'Absolute:', abspath(origfile)
        print

        # Run diff command.
        difffmt = 'diff -y --suppress-common-lines "%s" "%s" 2>&1'
        diffcmd = difffmt % (origfile, modfile)
        s, o = commands.getstatusoutput(diffcmd)

        rv = os.WEXITSTATUS(s)
        if rv == 0:
            print >> sys.stderr
            print >> sys.stderr, "Warning: no differences."
            print >> sys.stderr

        #print
        #print '_' * 80
        print o
        #print '_' * 80
        #print
        print

    rval = 0
    if not opts.dry_run:
        tmpf2 = tempfile.NamedTemporaryFile('w', prefix=tmpprefix)

        if not opts.no_confirm:
            cmd = ('%s --decision --merged-filename "%s" ' + \
                   '--title2 "NEW FILE" "%s" "%s" ') % \
                   (opts.command, tmpf2.name, origfile, modfile)
            s, o = commands.getstatusoutput(cmd)

        else:
            s, o = 0, 'NO_CONFIRM'

        if not opts.silent:
            if opts.diff:
                print o
            else:
                print o, origfile
        if o == 'ACCEPT' or o == 'NO_CONFIRM':
            backup(origfile, opts)
            if opts.checkout_clearcase:
                cc_checkout(origfile, opts)

            shutil.copyfile(modfile, origfile)
        elif o == 'REJECT' or o == 'NODECISION':
            rval = 1
        elif o == 'MERGED':
            if opts.diff:
                # run diff again to show the changes that have actually been
                # merged in the output log.
                diffcmd = difffmt % (origfile, tmpf2.name)
                s, o = commands.getstatusoutput(diffcmd)
                print 'Actual merged changes:'
                print
                print o
                print

            backup(origfile, opts)
            if opts.checkout_clearcase:
                cc_checkout(origfile, opts)

            shutil.copyfile(tmpf2.name, origfile)
        else:
            raise SystemExit("Error: unexpected answer from xxdiff: %s" % o)

        if opts.delete:
            try:
                os.unlink(modfile)
            except OSError, e:
                raise SystemExit("Error: deleting modified file (%s)" % str(e))

    return rval

#-------------------------------------------------------------------------------
#
def complete( parser ):
    "Programmable completion support. Script should work without it."
    try:
        import optcomplete
        optcomplete.autocomplete(parser)
    except ImportError:
        pass


#-------------------------------------------------------------------------------
#
def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip(), version=__version__)
    parser.add_option('--command', action='store', default='xxdiff',
                      help="xxdiff command prefix to use.")
    parser.add_option('-b', '--backup-type', action='store', type='choice',
                      choices=['parallel', 'other', 'none'], metavar="CHOICE",
                      default='none',
                      help="selects the backup type "
                      "('parallel', 'other', 'none')")
    parser.add_option('--backup-dir', action='store',
                      help="specify backup directory for type 'other'")
    parser.add_option('-C', '--checkout-clearcase', action='store_true',
                      help="checkout files with clearcase before storing.")
    parser.add_option('-n', '--dry-run', action='store_true',
                      help="print the commands that would be executed " +
                      "but don't really run them.")
    parser.add_option('-q', '--silent', '--quiet', action='store_true',
                      help="Do not output anything. Normally the decision "
                      "status and backup file location is output.")
    parser.add_option('-x', '--diff', action='store_true',
                      help="Run a diff and log the differences on stdout.")
    parser.add_option('-d', '--delete', action='store_true',
                      help="Instead of copying the temporary file, move it "
                      "(delete it after copying).")
    parser.add_option('-X', '--no-confirm', action='store_true',
                      help="do not ask for confirmation with graphical "
                      "diff viewer. This essentially generates a diff log and "
                      "copies the file over with backups.")
    complete(parser)
    opts, args = parser.parse_args()


    if not args or len(args) > 2:
        raise parser.error("you must specify exactly two files.")
    if len(args) == 1:
        if opts.delete:
            raise parser.error("no need to use --delete on file from stdin.")

        origfile, = args
        intmpf = tempfile.NamedTemporaryFile('w', prefix=tmpprefix)
        try:
            intmpf.write(sys.stdin.read())
            sys.stdin.close()
            intmpf.flush()
        except IOError, e:
            raise SystemExit(
                "Error: saving stdin to temporary file (%s)" % str(e))
        modfile = intmpf.name
    else:
        origfile, modfile = args

    if opts.silent and opts.diff:
        raise parser.error("you cannot ask for a diff output and for silent at "
                           "the same time.")
        
    if opts.backup_type == 'other':
        if not opts.backup_dir:
            opts.backup_dir = tempfile.mkdtemp(prefix=tmpprefix)
        print "Storing backup files under:", opts.backup_dir
    else:
        if opts.backup_dir:
            raise SystemExit("Error: backup-dir is only valid for backups of "
                             "type 'other'.")

    # call xxdiff and perform the conditional replacement.
    rval = cond_replace(origfile, modfile, opts)

    # repeat message at the end for convenience.
    if opts.backup_type == 'other' and opts.backup_dir:
        print
        print "Storing backup files under:", opts.backup_dir
        print

    return rval

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print >> sys.stderr, 'Interrupted.'
