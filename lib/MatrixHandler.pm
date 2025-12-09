package MatrixHandler;

use strict;
use warnings;
no strict 'vars';  # Allow old-style local variables
use utf8;
use Tex2UtfConfig;
use Records;
use OutputBuffer;
use LevelManager;
use MacroExpansion;

use Exporter 'import';
our @EXPORT = qw(
  matrix endmatrix endmatrixArg halign
);

sub matrix {
  LevelManager::start('endMatrix');
  LevelManager::start('endRow');
  LevelManager::start('endCell');
}

sub endmatrix {
  LevelManager::finish('endCell',1);
  trim(1);
  collapse(1);
  LevelManager::finish('endRow',1);
  # Now chunks correspond to rows of the matrix, records inside chunks to
  # Cells
  &halign(split(";",shift));
  LevelManager::finish('endMatrix',1);
}

sub endmatrixArg {
  &endmatrix(join(";",($_[0],split("",pop(@argStack)))));
}

# Takes a matrix in the following form: chunks on the last level
# are row of the matrix, records inside chunks are cells.
# Puts the resulting matrix in the first record on the given level
# and truncates the rest

# I'm trying to add parameters:
# length to insert between columns
# Array of centering options one for a column (last one repeated if needed)
# Currently supported:
#   c for center
#   r for right
#   l for left

sub halign {
  local($explength)=(shift);
  local(@c)=@_;
  local($last,$le,$b,$h);
  local(@w)=();
  #warn "levels @level, chunks @chunks, records @out\n";
  # Find metrics of cells
  for $r (0..$#chunks-$level[$#level]) {
    $last= ($r==$#chunks-$level[$#level]) ? $#out:
                                            $chunks[$r+1+$level[$#level]]-1;
  warn "Row $r: last column " . ($last-$chunks[$r+$level[$#level]]) ."\n"
                                if $debug & $debug_matrix;
    for $c (0..$last-$chunks[$r+$level[$#level]]) {
      ($h,$le,$b)=
                ($out[$chunks[$r+$level[$#level]]+$c] =~ /(\d+),(\d+),(\d+)/);
        # Format is Height:Length:Baseline
      $w[$c]=$le unless $w[$c]>$le;
    }
  }
  # expand the height and depth
  for $c (0..$#w-1) {$w[$c]+=$explength;}
  # Extend the @c array by the last element or "c" if it is empty
  @c=("c") x @w unless @c;
  @c=(@c,($c[$#c]) x (@w-@c));
  # Now expand the cells
  warn "Widths of columns @w\n" if $debug & $debug_matrix;
  for $r (0..$#chunks-$level[$#level]) {
    $last= ($r==$#chunks-$level[$#level]) ? $#out:
                                            $chunks[$r+1+$level[$#level]]-1;
    warn "Row $r: last column " . ($last-$chunks[$r+$level[$#level]]) ."\n"
        if $debug & $debug_matrix;
    for $c (0..$last-$chunks[$r+$level[$#level]]) {
      if ($c[$c] eq "c") {
        warn "Centering row $r col $c to width $w[$c]\n"
            if $debug & $debug_matrix;
        $out[$chunks[$r+$level[$#level]]+$c]=
          &center($w[$c],$out[$chunks[$r+$level[$#level]]+$c]);
      } elsif ($c[$c] eq "l") {
        warn "Expanding row $r col $c to width $w[$c]\n"
            if $debug & $debug_matrix;
        $out[$chunks[$r+$level[$#level]]+$c]=
          &join_records($out[$chunks[$r+$level[$#level]]+$c],
                &string2record(" " x
                  ($w[$c] - &get_length($out[$chunks[$r+$level[$#level]]+$c]))));
      } elsif ($c[$c] eq "r") {
        warn "Expanding row $r col $c to width $w[$c] on the left\n"
            if $debug & $debug_matrix;
        $out[$chunks[$r+$level[$#level]]+$c]=
          &join_records(&string2record(" " x
                  ($w[$c]-$explength-
                       &get_length($out[$chunks[$r+$level[$#level]]+$c]))),
                $out[$chunks[$r+$level[$#level]]+$c]);
        $out[$chunks[$r+$level[$#level]]+$c]=
          &join_records($out[$chunks[$r+$level[$#level]]+$c],
                &string2record(" " x $explength));
      } else {warn "Unknown centering option `$c[$c]' for halign";}
    }
  }
  # Now we creat rows
  collapseAll();
  # And stack them vertically
  for ($chunks[$level[$#level]]+1..$#out) {
    $out[$chunks[$level[$#level]]]=&vStack($out[$chunks[$level[$#level]]],
                                           $out[$_]);
  }
  &setbaseline($out[$chunks[$level[$#level]]],
               int((&get_height($out[$chunks[$level[$#level]]])-1)/2));
  $#chunks=$level[$#level];
  $#out=$chunks[$level[$#level]];
}

1;
