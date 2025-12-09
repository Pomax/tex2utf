package Tex2UtfConfig;

use strict;
use warnings;
use utf8;
use Getopt::Long;

use open ':std', ':encoding(UTF-8)';

BEGIN {
  if ($^O eq "MSWin32") {
    require Win32::Unicode::File;
    Win32::Unicode::File->import();
  }
}

# Export configuration variables
use Exporter 'import';
our @EXPORT = qw(
  $linelength $maxdef $debug $opt_by_par $opt_TeX $opt_ragged $opt_noindent
  $debug_flow $debug_record $debug_parsing $debug_length $debug_matrix
  $notusualtoks $notusualtokenclass $usualtokenclass $macro $active
  $tokenpattern $multitokenpattern $secondtime
  parse_options false
);

# Configuration variables
our $linelength = 150;
our $maxdef = 400;
our $debug = 0;
our $opt_by_par = 0;
our $opt_TeX = 1;
our $opt_ragged = 0;
our $opt_noindent = 0;

# Debug flags
our $debug_flow = 1;
our $debug_record = 2;
our $debug_parsing = 4;
our $debug_length = 8;
our $debug_matrix = 16;

# Token patterns
our $notusualtoks = "\\\\" . '\${}^_~&@';
our $notusualtokenclass = "[$notusualtoks]";
our $usualtokenclass = "[^$notusualtoks]";
our $macro = '\\\\([^a-zA-Z]|([a-zA-Z]+\s*))'; # Why \\\\? double interpretation!
our $active = "$macro|\\\$\\\$|$notusualtokenclass";
our $tokenpattern = "$usualtokenclass|$active";
our $multitokenpattern = "$usualtokenclass+|$active";

# Runtime state
our $secondtime = 0;

# Make false work
sub false { 0 }

sub parse_options {
  GetOptions(
    "linelength=s" => \$linelength,
    "maxdef=s" => \$maxdef,
    "debug" => \$debug,
    "by_par" => \$opt_by_par,
    "TeX" => \$opt_TeX,
    "ragged" => \$opt_ragged,
    "noindent" => \$opt_noindent
  ) or die "Could not parse provided runtime flag(s)";
}

1;
