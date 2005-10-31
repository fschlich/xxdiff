/******************************************************************************\
 * $Id: exceptions.cpp 294 2001-10-21 07:27:43Z blais $
 * $Date: 2001-10-21 03:27:43 -0400 (Sun, 21 Oct 2001) $
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

/*==============================================================================
 * EXTERNAL DECLARATIONS
 *============================================================================*/

#include <exceptions.h>
#include <help.h>

#include <iostream>
#include <string.h> // strerror
#include <stdlib.h>
#include <errno.h>


XX_NAMESPACE_BEGIN


/*==============================================================================
 * PUBLIC FUNCTIONS
 *============================================================================*/

/*==============================================================================
 * CLASS XxError
 *============================================================================*/

//------------------------------------------------------------------------------
//
XxError::XxError( 
   XX_EXC_PARAMS_DECL(file,line),
   const QString& msg
)
{
   QTextOStream oss( &_msg );
   oss << "Xxdiff error (" << file << ":" << line << "): ";
   if ( !msg.isEmpty() ) {
      oss << msg;
   }
}

//------------------------------------------------------------------------------
//
XxError::~XxError() XX_THROW_NOTHING
{}

//------------------------------------------------------------------------------
//
const QString& XxError::getMsg() const XX_THROW_NOTHING
{
   return _msg;
}

/*==============================================================================
 * CLASS XxUsageError
 *============================================================================*/

//------------------------------------------------------------------------------
//
XxUsageError::XxUsageError( 
   XX_EXC_PARAMS_DECL(file,line),
   const QString& msg,
   bool           benine,
   bool           version
) :
   XxError( file, line, msg ),
   std::domain_error( "Usage error." ),
   _benine( benine )
{
   if ( version == false ) {
      QTextStream oss( &_msg, IO_WriteOnly | IO_Append );
      oss << endl;
      XxHelp::dumpUsage( oss );
   }
   else {
      // Overwrite base class msg.
      QTextStream oss( &_msg, IO_WriteOnly );
      XxHelp::dumpVersion( oss );      
   }
}

//------------------------------------------------------------------------------
//
bool XxUsageError::isBenine() const
{
   return _benine;
}

/*==============================================================================
 * CLASS XxIoError
 *============================================================================*/

//------------------------------------------------------------------------------
//
XxIoError::XxIoError( 
   XX_EXC_PARAMS_DECL(file,line),
   const QString& msg 
) :
   XxError( file, line, msg ),
   std::runtime_error( strerror( errno ) )
{
   QTextStream oss( &_msg, IO_WriteOnly | IO_Append );
   oss << endl;
   oss << "IO error... " << strerror( errno );
}

/*==============================================================================
 * CLASS XxInternalError
 *============================================================================*/

//------------------------------------------------------------------------------
//
XxInternalError::XxInternalError( 
   XX_EXC_PARAMS_DECL(file,line)
) :
   XxError( file, line ),
   std::runtime_error( "Internal error." )
{
   QTextStream oss( &_msg, IO_WriteOnly | IO_Append );
   oss << endl;
   oss << "Internal error." << endl << endl;
   oss << "There has been an internal error within xxdiff." << endl
       << "To report bugs, please use the sourceforge bug tracker" << endl
       << "at http://sourceforge.net/tracker/?group_id=2198" << endl
       << "and log the above information above and if possible," << endl
       << "the files that caused the error, and as much detail as" << endl
       << "you can to reproduce the error.";
   oss << endl << flush; // for extra space

// We need this because somehow when called from an activate signal the catch
// handler is not working properly and the app dumps core.  At least this way
// I'll know what's going on at least when developing in debug mode.
#ifdef XX_DEBUG
   std::cerr << "Throwing exception:" << std::endl;
   std::cerr << _msg.latin1() << std::endl;
#endif
}

XX_NAMESPACE_END

