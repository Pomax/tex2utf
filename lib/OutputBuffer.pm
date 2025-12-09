package OutputBuffer;

use strict;
use warnings;
no strict 'vars';  # Allow old-style local variables
use utf8;
use Tex2UtfConfig;
use Records;

use Exporter 'import';
our @EXPORT = qw(
  @out @chunks @level @tokenByToken @wait @action $curlength
  $c1 $c2 $re $fr
  output_print prepare_cut commit uncommit exp_sp finishBuffer
);

# Output buffer state
our @out = ();
our @chunks = (0);
our @level = (0);
our @tokenByToken = (0);
our @wait = ();
our @action = ();
our $curlength = 0;

# Space expansion variables
our ($c1, $c2, $re, $fr);

# Used to expand spaces

sub exp_sp {$c1++;$c2=0 if $c1>$re; return " " x ($c2+$fr+1);}

# Outputs the outermost level of the output list (until the start of level 1)
# If gets a true argument, does not expand spaces

sub output_print {
  warn "Printing...\n" if $debug & $debug_flow;
  local($last,$l,$exp) = ($#level? $chunks[$level[1]]-1: $#out);
  ($last >=0) || return;
  $l=&get_length($out[0]);
  if ($last >= 1) {
    for (1..$last) {
      $l += &get_length($out[$_]);
    }
  }
  if ($debug & $debug_length)  {
    if ($l != $curlength) {
      for (0..$last) {
        warn "Wrong lengths Record $_ $out[$_]\n__ENDREC__\n" ;
      }
    }
  }
  $curlength=$l;
  warn "l=$l, linelength=$linelength, curlength=$curlength\n"
    if $debug & $debug_length;
 IF_L:
 {
  if (!shift && ($l=$linelength-$curlength)>=0) {
    warn "entered branch for long string\n"
      if $debug & $debug_length;
    $exp=0;
    (($out[$last] =~ s/\s+$//) && ($l+=length($&)))
        if $out[$last] =~ /^0,/;
    warn "l=$l with whitespace\n"
      if $debug & $debug_length;
    last IF_L if $l<=0;
    local($str,$h,$fr,$re,$c1,$c2,@t);
    for (0..$last) {
      ($str,$h)=(split(/,/,$out[$_],5))[4,0];
      (@t = ($str =~ /( )/g), $exp+=@t) if (!$h);
    }
    if ($exp) {
      $re=$l % $exp;
      $fr=int(($l-$re)/$exp);
      warn "$l Extra spaces in $exp places, Fr=$fr," .
          " Remainder=$re, LL=$linelength, CL=$curlength\n" if $debug & $debug_length;
      $c1=0;
      $c2=1;
      for (0..$last) {
        ($str,$h)=(split(/,/,$out[$_],5))[4,0];
        unless ($h || $opt_ragged) {
          $str =~ s/ /&exp_sp/ge;
          $out[$_]=&string2record($str);
        }
      }
    }
  }
  else {warn "Do not want to expand $l spaces\n" if $debug & $debug_length;}
 }
  if ($last >= 1) {
    for (1..$last) {
      $out[0] = &join_records($out[0],$out[$_]);
    }
  }
  $l=&get_length($out[0]);
  warn "LL=$linelength, CurL=$curlength, OutL=$l\n" if $debug & $debug_length;
  &printrecord($out[0]);
  $curlength=0;
  if ($#out>$last) {
    @out=@out[$last+1..$#out];
    for (0..$#chunks) {$chunks[$_] -= $last+1;}
  } else {
    @out=();
  }
  if ($#level) {
    splice(@chunks,1,$level[1]-2);
  } else {
    @chunks=(0);
  }
}

# Cuts prepared piece and arg into printable parts (unfinished)
# Suppose that level==0

sub prepare_cut {
  warn "Preparing to cut $_[0]\n" if $debug & $debug_flow;
  warn "B:Last chunk number $#chunks, last record $#out\n" if $debug & $debug_flow;
  (warn "\$#level non 0", return $_[0]) if ($#level!=0);
  local($lenadd)=(&get_length($_[0]));
  local($lenrem)=($linelength-$curlength);
  if ($lenadd+$curlength<=$linelength) {
    warn "No need to cut, extra=$lenrem\n" if $debug & $debug_flow;
    return $_[0];
  }
  # Try to find a cut in the added record before $lenrem
  local($rec)=@_;
  local($h,$str,$ind,@p)=(split(/,/,$rec,5))[0,4];
  local($good)=(0);
  if ($h<2) {
    while ($lenrem<$lenadd && ($ind=rindex($str," ",$lenrem))>-1) {
      warn "Cut found at $ind, lenrem=$lenrem\n" if $debug & $debug_flow;
      $good=1;
      # $ind=1 means we can cut 2 chars
      @p= &cut($ind+1,$rec);
      warn "After cut: @p\n" if $debug & $debug_record;
      push(@out,$p[0]);
      $curlength+=$ind+1;
      &output_print();
      $rec=$p[1];
      ($lenadd,$str)=(split(/,/,$rec,5))[1,4];
      $lenrem=$linelength;
    }
    return $rec if $good;
  }
  # If the added record is too long, there is no sense in cutting
  # things we have already, since we will cut the added record anyway...
  local($forcedcut);
  if ($lenadd > $linelength && $lenrem) {
      @p= &cut($lenrem,$rec);
      warn "After forced cut: @p\n" if $debug & $debug_record;
      push(@out,$p[0]);
      $curlength+=$lenrem;
      &output_print();
      $rec=$p[1];
      ($lenadd,$str)=(split(/,/,$rec,5))[1,4];
      $lenrem=$linelength;
  }
  # Now try to find a cut before the added record
  if ($#out>=0 && !$forcedcut) {
    for (0..$#out) {
      ($h,$str)=(split(/,/,$out[$#out-$_],5))[0,4];
      if ($h<2 && ($ind=rindex($str," "))>-1 && ($ind>0 || $_<$#out)) {
        warn "Cut found at $ind, in chunk $#out-$_\n"
            if $debug & $debug_flow;
        # split at given position
        @p=&cut($ind+1,$out[$#out-$_]);
        $out[$#out-$_]=$p[0];
        @p=($p[1],@out[$#out-$_+1..$#out]);
        @out=@out[0..$#out-$_];
        warn "\@p is !", join('!', @p), "!\n\@out is !", join('!', @out), "!\n"
          if $debug & $debug_flow;
        &output_print();
        warn "did reach that\n"
          if $debug & $debug_length;
        @out=@p;
        $good=1;
        $curlength=0;
        for (@out) {$curlength+=&get_length($_);}
        last;
      }
      warn "did reach wow-this\n"
      if $debug & $debug_length;
    }
    warn "did reach this\n"
      if $debug & $debug_length;
  }
  return &prepare_cut if $good;
  warn "No cut found!\n" if $debug & $debug_flow;
  # If anything else fails use force
  &output_print();
  while (&get_length($rec)>$linelength) {
    @p=&cut($linelength,$rec);
    @out=($p[0]);
    &output_print();
    $rec=$p[1];
  }
  $curlength=0;
  return $rec;
}

# Adds a record to the output list

sub commit {
  warn "Adding $_[0]\n" if $debug & $debug_flow;
  warn "B:Last chunk number $#chunks, last record $#out\n" if $debug & $debug_flow;
  local($rec)=@_;
  if ($#level==0) {
    local($len)=&get_length($_[0]);
    if ($curlength+$len>$linelength) {
      $rec=&prepare_cut;
      $len=&get_length($rec);
    }
    $curlength+=$len;
  }
  push(@out,$rec);
  if ($#out!=$chunks[$#chunks]) {push(@chunks,$#out);}
  warn "a:Last chunk number $#chunks, last record $#out, the first chunk\n" if $debug & $debug_flow;
  warn " on the last level=$#level is $level[$#level], waiting for $wait[$#level]\n" if $debug & $debug_flow;
  if ($#level && defined $wait[$#level] && $wait[$#level] =~ /^\d+$/ && $wait[$#level] == $#chunks-$level[$#level]+1) {
    local($sub,$arg)=($action[$#level]);
    if ($sub eq "") {
      require LevelManager;
      LevelManager::finish($wait[$#level]);
    }
    else {
      require MacroExpansion;
      MacroExpansion::callsub($sub);
    }
  }
  warn "curlength=$curlength on level=$#level\n" if $debug & $debug_length;
}

# Simulates Removing a record from the output list (unfinished)

sub uncommit {
  warn "Deleting...\n" if $debug & $debug_flow;
  warn "B:Last chunk number $#chunks, last record $#out\n" if $debug & $debug_flow;
  (warn "Nothing to uncommit", return) if $#out<0;
  if ($#level==0) {
    local($len)=&get_length($out[$#out]);
    $curlength-=$len;
  }
  local($rec);
  $rec=$out[$#out];
  $out[$#out]=&empty();
  warn "UnCommit: now $chunks[$#chunks] $rec\n__ENDREC__\n"
      if $debug & $debug_record;
  warn "a:Last chunk number $#chunks, last record $#out, the first chunk\n" if $debug & $debug_flow;
  warn " on the last level=$#level is $level[$#level], waiting for $wait[$#level]" if $debug & $debug_flow;
  warn "curlength=$curlength on level=$#level\n" if $debug & $debug_length;
  return $rec;
}

sub finishBuffer {
  require LevelManager;
  while ($#level > 0) {
    LevelManager::finish("");
  }
  &output_print(1);
}

1;
