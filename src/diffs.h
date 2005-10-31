/******************************************************************************\
 * $Id: diffs.h 138 2001-05-20 18:08:45Z blais $
 * $Date: 2001-05-20 14:08:45 -0400 (Sun, 20 May 2001) $
 *
 * Copyright (C) 1999-2001  Martin Blais <blais@iro.umontreal.ca>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 *
 *****************************************************************************/

#ifndef INCL_XXDIFF_DIFFS
#define INCL_XXDIFF_DIFFS

/*==============================================================================
 * EXTERNAL DECLARATIONS
 *============================================================================*/

#ifndef INCL_XXDIFF_LINE
#include <line.h>
#endif

#ifndef INCL_XXDIFF_DEFS
#include <defs.h>
#endif

#ifndef INCL_QT_QOBJECT
#include <qobject.h>
#define INCL_QT_QOBJECT
#endif

#ifndef INCL_STD_VECTOR
#include <vector>
#define INCL_STD_VECTOR
#endif

#ifndef INCL_STD_MEMORY
#include <memory>
#define INCL_STD_MEMORY
#endif

#ifndef INCL_STD_IOSFWD
#include <iosfwd>
#define INCL_STD_IOSFWD
#endif


XX_NAMESPACE_BEGIN


/*==============================================================================
 * FORWARD DECLARATIONS
 *============================================================================*/

class XxBuffer;



/*==============================================================================
 * CLASS XxDiffs
 *============================================================================*/

// <summary> a class to build the diffs data structure </summary>

class XxDiffs : public QObject {

   Q_OBJECT

public:

   /*----- types and enumerations -----*/

   struct SeaResult {

      /*----- member functions -----*/

      // Construtor for invalid search result.
      SeaResult();

      // Constructor.
      SeaResult( const XxDln lineNo, const XxFln fline[3] );

      // Returns true if valid.
      bool isValid() const;

      /*----- data members -----*/

      XxDln _lineNo;
      XxFln _fline[3];
   };

   /*----- member functions -----*/

   // Constructor which builds an empty diffs.
   XxDiffs();

   // Constructor.
   XxDiffs( std::vector<XxLine>& lines, bool isDirectoryDiff = false );

   // Destructor.
   virtual ~XxDiffs();

   // Returns the number of display lines.
   uint getNbLines() const;

   // Returns the number of lines that have selected content (i.e. either just
   // have content, or have a selected side with content).  Counts the number of
   // times we encountered new unselected changes (for merged view).
   uint getNbLinesWithContent( uint& unselectedChanges ) const;

   // Moves backwards nbLines lines from a specified starting line of the diffs,
   // counting only visible lines according to the current selection, counting
   // unselected changes (undecided regions) as unselChangesLines lines each.
   // Talk about a specialized function!  This one is for the merged view
   // scrollbar resizing.  It returns the line number of the top visible line.
   XxDln moveBackwardsVisibleLines(
      XxDln startingLine,
      uint  nbLines,
      uint  unselChangesLines
   ) const;

   // Returns a display line.  Remember that lines start counting at 1.  Note:
   // be careful with the non-const version, if you change the line's state
   // yourself, you need to call for a redraw.
   const XxLine& getLine( const XxDln lineno ) const;

   // Given a file line number in a specific file, returns the display line no.
   XxDln getDisplayLine( const XxFln fline, const XxFno fno ) const;

   // Applies a selection to a line.
   void selectLine( XxDln lineNo, XxLine::Selection selection );

   // Applies a selection to a set of lines whose type is contiguous.
   void selectRegion( XxDln lineNo, XxLine::Selection selection );

   // Applies a selection globally.
   void selectGlobal( XxLine::Selection selection );
   
   // Applies a selection globally, to unselected regions only.
   void selectGlobalUnselected( XxLine::Selection selection );

   // Returns the extents and type of a region that contains a certain line no.
   // <group>
   XxLine::Type findRegion( 
      XxDln  lineNo, 
      XxDln& regionStart,
      XxDln& regionEnd
   ) const;
   // </group>

   // Returns the extents and type of a region that contains a certain line
   // no. and that has the same selection properties.
   // <group>
   XxLine::Type findRegionWithSel( 
      XxDln  lineNo, 
      XxDln& regionStart,
      XxDln& regionEnd
   ) const;
   // </group>

   // Splits, swaps or joins two neighboring compatible regions.  More
   // precisely:  if the region which contains the given line contains text
   // everywhere, it is split in a certain direction; if the region which
   // contains the given line contains text only on one side AND has a
   // neighboring region which has text only on the other side, then the regions
   // are swapped in order; and if those regions have already been swapped, they
   // are joined again.  Return true if the operation was a join.
   bool splitSwapJoin( XxDln lineNo, uint nbFiles );

   // Searches for the next/previous difference region.  Returns -1 if not
   // found.
   // <group>
   XxDln findNextDifference( XxDln lineNo ) const;
   XxDln findPreviousDifference( XxDln lineNo ) const;
   // </group>

   // Searches for the next/previous unselected region.  Returns -1 if not
   // found.
   // <group>
   XxDln findNextUnselected( XxDln lineNo ) const;
   XxDln findPreviousUnselected( XxDln lineNo ) const;
   // </group>

   // Returns the number of non-blank lines between start and end.
   uint getNbFileLines( 
      XxFno no,
      XxDln start,
      XxDln end
   ) const;

   // Returns the closest (floor) file line for the given display line.  The
   // actuallyEmpty parameter is set to true if that line is actually empty for
   // that file no.
   XxFln getFileLine( 
      XxFno no,
      XxDln lineNo,
      bool& actuallyEmpty
   ) const;

   // Dirty bit management.  The diffs become dirty if selection changes. 
   // <group>
   void clearDirty();
   bool isDirty() const;
   // </group>

   // Returns true if is at least one line that has been selected.
   bool isSomeSelected() const;

   // Returns false if there are still some unselected lines.
   bool isAllSelected() const;

   // Save merged with selected regions.  If there are still some unselected
   // regions it will return false but save anyway.
   bool save( 
      std::ostream&                  os, 
      const std::auto_ptr<XxBuffer>* files,
      bool                           useConditionals,
      const std::string&             conditional1,
      const std::string&             conditional2
   ) const;

   // Save selected lines with an appropriate prefix.  Returns true if there
   // were some regions saved (false thus means an empty file).
   bool saveSelectedOnly( 
      std::ostream& os, 
      const std::auto_ptr<XxBuffer>* files
   ) const;

   // Searches for the occurence of the search text in the files and sets the
   // diff lines where the text appears in either, and for each diff line, in
   // which file the line is found.
   void search( 
      const char*                    searchText,
      const int                      nbFiles,
      const std::auto_ptr<XxBuffer>* files
   );

   // Returns the search results.
   const std::vector<SeaResult>& getSearchResults() const;

   // Finds the next/previous search results.
   // <group>
   SeaResult findNextSearch( XxDln lineNo ) const;
   SeaResult findPreviousSearch( XxDln lineNo ) const;
   // </group>

   // Initialize horizontal diffs for lines.
   void initializeHorizontalDiffs(
      const std::auto_ptr<XxBuffer>* files,
      const bool                   force = false
   );

   // Automatically merge by performing selections on file1, assuming order
   // "mine older yours", and leaving conflicts unselected.
   void merge();

   // Check if all selections are of the specified no.  If so return true.
   bool checkSelections( const XxLine::Selection sel ) const;

   // Returns true if this diffs is a directory diffs.
   bool isDirectoryDiff() const;

   // Dump debug output.
   std::ostream& dump( std::ostream& ) const;

signals:

   /*----- member functions -----*/

   void changed();
   void nbLinesChanged();


private:

   /*----- member functions -----*/

   // This is simply a non-const version of getLine().  It barfs with MIPSpro
   // 7.3 if it overloads the public const version so the name had to be
   // changed.
   XxLine& getLineNC( const XxDln lineno );

   // Split region into a new set of lines.  Push new lines onto given vector.
   // This is a convenience method.
   void splitTwoRegions(
      std::vector<XxLine>& newLines, 
      XxDln                start,
      XxDln                end,
      XxFno                s1,
      XxFno                s2
   ) const;

   // Make really sure the line numbers are sequential.  This is zealous and
   // that's how I like it.
   void validateLineNumbers() const;

   /*----- data members -----*/

   // list of line descriptors
   std::vector< XxLine >    _lines;

   std::vector< SeaResult > _searchResults;

   bool                     _initializedHorizontalDiffs;
   bool                     _isDirectoryDiff;
   bool                     _dirty;

};


XX_NAMESPACE_END

#include <diffs.inline.h>

#endif
