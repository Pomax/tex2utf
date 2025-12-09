#!/usr/local/bin/perl

# $Id: run.pl, v 1.0 2024/12/09 00:00:00 Refactored $
#
# Refactored version of tex2utf.pl split into modular components
#
# Original UTF8-massaged version of https://ctan.org/pkg/tex2mail
# Rewritten October 2020 by pomax@nihongoressources.com

use strict;
use warnings;
use utf8;

# Add lib directory to module search path
use lib 'lib';

# Import all modules
use Tex2UtfConfig;
use Records;
use OutputBuffer;
use LevelManager;
use MacroExpansion;
use TeXHandlers;
use MatrixHandler;
use TeXDefinitions;
use Parser;

# Parse command line options
Tex2UtfConfig::parse_options();

# Initialize TeX type definitions
TeXDefinitions::initialize_definitions();

# Get input file from command line arguments
my $input_file = shift @ARGV;
if ($input_file) {
  open(STDIN, '<:encoding(UTF-8)', $input_file) or die "Cannot open input file '$input_file': $!";
}

# =============================
#   Run the script by looping
# paragraph parsing until there
#   is nothing left to parse.
# =============================

$/ = $Tex2UtfConfig::opt_by_par ? "\n\n" : ''; # whole paragraph mode
while (Parser::paragraph()) { }
OutputBuffer::finishBuffer();

__END__

# History:
# Jul 98: \choose added, fixed RE for \noindent, \eqalign and \cr.
#         \proclaim and better \noindent added.
# Sep 98: last was used inside an if block, was leaking out.
# Jan 00: \sb \sp
# Feb 00: remove extraneous second EOF needed at end.
          remove an empty line at end of output
          New option -by_par to support per-paragraph processing
          New option -TeX which support a different \pmatrix
          New option -ragged to not insert whitespace to align right margin.
          New option -noindent to not insert whitespace at beginning.
          Ignore \\ and \cr if followed by \end{whatever}.
          Ignore \noindent if not important.
          Ignore whitespace paragraphs.
# Apr 00: Finishing a level 1 would not merge things into one chunk.
# May 00: Additional argument to finish() to distinguish finishing
          things which cannot be broken between lines.
# Sep 00: Add support for new macro for strings with screen escapes sequences:
          \LITERALnoLENGTH{escapeseq}.
# Oct 00: \LITERALnoLENGTH can have a chance to work in the baseline only;
          in fact the previous version did not work even there...
          If the added record is longer than line length, do not try to
          break the line before it...

# --------------------- switchover from tex2mail to tex2utf --------------------

# Oct 20: rewrote parts of the script to yield a better text form by using
          modern unicode characters instead of ASCII art.
# Jan 22: added a &paragraph preprocess step to remove everything before
          the \begin{document} command, as it doesn't get consulted anyway,
          but will happily pollute the output.

# --------------------- refactored into separate modules --------------------

# Dec 24: refactored tex2utf.pl into separate modules for better organization
          and maintainability.
