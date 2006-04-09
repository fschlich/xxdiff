#!/usr/bin/env python
# This file is part of the xxdiff package.  See xxdiff for license and details.

# If this file is found independently as svn-foreign, here are the licensing
# terms:
#
#  svn-foreign
#  Copyright (C) 2006  Martin Blais
#  URL:  http://furius.ca/xxdiff/
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""svn-foreign [<options>] [<dir> ...]

This script deals with the common case where you have developed something using
Subversion and you have forgotten some unregistered files before committing.

svn-foreign runs 'svn status' on the given Subversion-managed directories, to
find out which files are unaccounted for and for each of these files, it asks
you what to do with it::

   [a] add it,
   [d] delete it
   [m] set an svn:ignore property on its parent directory to mask it
   [i] ignore and leave it where it is

The script works interactively and is meant to allow you to quickly deal with
the forgotten files in a subversion checkout.  It works with directories as
well.

"""
# Notes
# -----
# We need to make sure that this file remains independently working from the
# rest of xxdiff, i.e. even though some features may not be available, it should
# always be working without xxdiff.  This is because this file may be
# distributed under the simple name svn-foreign, and run independently, even if
# you have not the xxdiff infrastructure.
#
# Future Work
# -----------
#
# - We could implement backups for the deleted files (with lazy creation of
#   backup directory).
#
# Credits
# -------
# * To Sean Reifschneider (Jafo) for providing example code for raw tty input


__version__ = '$Revision$'
__author__ = 'Martin Blais <blais@furius.ca>'


# stdlib imports
import sys, os, termios, tty, shutil, tempfile
from subprocess import Popen, PIPE, call
from os.path import *


#-------------------------------------------------------------------------------
#
debug = False

#-------------------------------------------------------------------------------
#
def read_one():
    """
    Reads a single character from the terminal.
    """
    # Set terminal in raw mode for faster input.
    orig_term_attribs = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())
    try:
        c = sys.stdin.read(1)
        if c == chr(3): # INTR
            raise KeyboardInterrupt
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH,
                          orig_term_attribs)
    return c

#-------------------------------------------------------------------------------
#
def add( fn ):
    """
    Add the file into Subversion.
    """
    call(['svn', 'add', fn])

#-------------------------------------------------------------------------------
#
def delete( fn ):
    """
    Delete the file or directory (recursively) from the checkout.
    """
    if isdir(fn):
        rmrf(fn)
    else:
        os.unlink(fn)

def rmrf( fnodn ):
    """
    Delete the given directory and all its contents.
    """
    if not exists(fnodn):
        return

    if isdir(fnodn):
        for root, dirs, files in os.walk(fnodn, topdown=False):
            for fn in files:
                os.remove(join(root, fn))
            for dn in dirs:
                adn = join(root, dn)
                if islink(adn):
                    os.remove(adn)
                else:
                    os.rmdir(adn)
        os.rmdir(root)
    else:
        os.remove(fnodn)

#-------------------------------------------------------------------------------
#
def ignore_prop( dn, ignores ):
    """
    Set svn:ignore on directory 'dn'.
    """
    f = tempfile.NamedTemporaryFile('w')
    f.write(ignores)
    f.flush()
    call(['svn', 'propset', 'svn:ignore', '-F', f.name, dn])
    f.close()


#-------------------------------------------------------------------------------
#
def filter2( predicate, *arguments ):
    ein, eout = [], []
    for args in zip(*arguments):
        add_args = args
        if len(args) == 1:
            add_args = args[0]

        if predicate(*args):
            ein.append(add_args)
        else:
            eout.append(add_args)
    return ein, eout


#-------------------------------------------------------------------------------
#
def parse_options():
    """
    Parse the options.
    """
    import optparse
    parser = optparse.OptionParser(__doc__.strip())

    parser.add_option('-c', '--commit', action='store',
                      help="Ask to commit after running, with given comments.")

    parser.add_option('-C', '--commit-without-comment', action='store_const',
                      dest='commit', const='',
                      help="Ask to commit after running, with given comments.")

    parser.add_option('-q', '--quiet', '--silent', action='store_true',
                      help="Suppress certain harmless warnings.")

    opts, args = parser.parse_args()

    return opts, args


#-------------------------------------------------------------------------------
#
def query_unregistered_svn_files( filenames, quiet=True, output=sys.stdout ):
    """
    Runs an 'svn status' command, and then loops over all the files that are not
    registered, asking the user one-by-one what action to take (see this
    module's docstring for more details).

    Return True upon completion.  Anything else signals that the user has
    interrupted the procedure.
    """
    write = output.write
    
    # If there are multiple args--such as *--filter out the non svn directories.
    dirs, files = filter2(isdir, filenames)
    if len(dirs) > 1:
        svndirs = [x for x in dirs if isdir(join(x, '.svn'))]
        if svndirs != dirs:
            if not quiet:
                for dn in set(dirs) - set(svndirs):
                    write("Warning: skipping non-checkout dir '%s'\n" % dn)
            filenames = svndirs + files

    # Run svn status to find the files that are unaccounted for
    cmd = ['svn', 'status'] + filenames
    if debug:
        write(' '.join(cmd))
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise SystemExit("Error: %s" % err)

    # Get out if there is nothing to do.
    if not out.strip():
        write('(Nothing to do.)\n')
        return True

    # Print the output of the status command for the user's excitement
    write('Status\n------\n')
    write(out)
    write('\n')

    # Process foreign files
    for line in out.splitlines():
        if line[0] == '?':
            fn = line[7:]

            # Get the file size.
            size = os.lstat(fn).st_size
            ftype = ''
            if islink(fn):
                ftype = '(symlink)'

            # Command loop (one command)
            while True:
                write('[Add|Del|Mask|Ign|View|Quit]  %10d  %s %s ? ' %
                      (size, fn, ftype))

                # Read command
                c = read_one().lower()
                write(c)
                write('\n')

                if c == 'a': # Add
                    add(fn)
                    break

                elif c == 'd': # Delete
                    delete(fn)
                    break

                elif c == 'm': # Mask
                    dn, bn = split(fn)
                    if dn == '':
                        dn = '.'

                    # Get the properties first
                    p = Popen(['svn', 'propget', 'svn:ignore', dn],
                              stdout=PIPE, stderr=PIPE)
                    svnign, err = p.communicate()
                    if p.returncode != 0:
                        raise SystemExit(err)

                    # Sanitize the svn:ignore contents a bit
                    if svnign:
                        svnign = svnign.rstrip() + '\n'

                    write("--(current svn:ignore on '%s')--\n" % dn)
                    write(svnign)
                    write('----------------------------\n')

                    write("Add pattern (! to cancel, default: [%s]):" % bn)
                    pat = raw_input()
                    if pat == '':
                        pat = bn
                    if pat != '!':
                        svnign += pat + '\n'
                        ignore_prop(dn, svnign)

                        write('----------------------------\n')
                        write(svnign)
                        write('----------------------------\n')

                        break

                elif c == 'i': # Ignore
                    break

                elif c in ['q', 'x']: # Quit/exit
                    write('(Quitting.)\n')
                    return False

                elif c in 'v': # View
                    # Call on 'more' to view the file
                    write('-' * 80 + '\n')
                    pager = os.environ.get('PAGER', '/bin/more')
                    call([pager, fn])
                    # Look again

                elif c == chr(12): # Ctrl-L: Clear
                    # FIXME: is there a way to do this directly on the terminal?
                    call(['clear'])

                else: # Loop again
                    write('(Invalid answer.)\n')

    write('(Done.)\n')
    return True

    
#-------------------------------------------------------------------------------
#
def main():
    """
    Main program.
    """
    opts, args = parse_options()

    # Run the main loop...
    if query_unregistered_svn_files(args, opts.quiet, sys.stdout) != True:
        # The user has quit.
        sys.exit(0)

    # Commit the files if requested.
    if opts.commit is not None:
        # Command loop (one command)
        sys.stdout.write('Commit? [Yes|No/Quit] ')

        # Read command
        c = read_one().lower()
        print c

        if c == 'y': # Commit, without comments.
            call(['svn', 'commit', '-m', opts.commit] + args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print
