package LevelManager;

use strict;
use warnings;
no strict 'vars';  # Allow old-style local variables
use utf8;
use Tex2UtfConfig;
use Records;
use OutputBuffer;

use Exporter 'import';
our @EXPORT = qw(
  start finish finish_ignore collapse collapseOne collapseAll
  assertHave trim trim_one trim_beg trim_end
);

# Begin a new level with waiting for $event
# Special events: If number, wait this number of chunks

sub start {
  warn "Beginning with $_[0], $_[1]\n" if $debug & $debug_flow;
  warn "B:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  if ($chunks[$level[$#level]] <= $#out && $chunks[$#chunks] <= $#out) {
    # the last level is non empty
    push(@chunks, $#out + 1);
  }
  push(@level, $#chunks);
  push(@tokenByToken, 0);
  $wait[$#level] = shift;
  if ($#_<0) { $action[$#level] = ""; } else { $action[$#level] = shift; }
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
}

# finish($event, $force_one_group)
# Finish the inner scope with the event $event. If this scope is empty,
# add an empty record.  If finishing the group would bring us to toplevel
# and $force_one_group is not set, can break things into chunks to improve
# line-breaking.
# No additional action is executed

sub finish {
  warn "Finishing with $_[0]\n" if $debug & $debug_flow;
  local($event,$len,$rec)=(shift);
  if (($wait[$#level] ne "") && ($wait[$#level] ne $event)) {
    warn "Got `$event' while waiting for `$wait[$#wait]', rest=$Parser::par";
  }
  warn "Got finishing event `$event' in the outermost block, rest=$Parser::par"
      unless $#level;
  if ($#out<$chunks[$level[$#level]]) {push(@out,&empty);}
  # Make anything after $level[$#level] one chunk if there is anything
  warn "B:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  $#chunks=$level[$#level]; #if $chunks[$level[$#level]]<=$#out;
  local(@t);
  if ($#level==1 && !$_[0]) {
    @t=@out[$chunks[$#chunks]..$#out];
    $#out=$chunks[$#chunks]-1;
  }
  $#level--;
  $#action--;
  $#tokenByToken--;
  $#wait--;
  if ($#level==0 && !$_[0]) {
    for (@t) {&commit($_);}
  }
  warn
      "a:Last $#chunks, the first on the last level=$#level is $level[$#level]"
           if $debug & $debug_flow;
  if ($wait[$#level] == $#chunks-$level[$#level]+1) {
    local($sub)=($action[$#level]);
    if ($sub eq "") {&finish($wait[$#level]);}
    else {
      require MacroExpansion;
      MacroExpansion::callsub($sub);
    }
  }
}

# finish level and discard it

sub finish_ignore {
  warn "Finish_ignoring with $_[0]\n" if $debug & $debug_flow;
  local($event,$len)=(shift);
  if (($wait[$#level] ne "") && ($wait[$#level] ne $event)) {
    warn "Got `$event' while waiting for `$wait[$#wait]', rest=$Parser::par";
  }
  warn "Got finishing event `$event' in the outermost block, rest=$Parser::par" unless $#level;
  $#out=$chunks[$level[$#level]]-1;
  pop(@level);
  pop(@tokenByToken);
  pop(@action);
  pop(@wait);
}

# Asserts that the given number of chunks exists in the last level

sub assertHave {
  local($i,$ii)=(shift);
  if (($ii=$#chunks-$level[$#level]+1)<$i) {
    warn "Too few chunks ($ii) in inner level, expecting $i";
    return 0;
  }
  return 1;
}

# Takes the last ARGUMENT chunks, collapse them to records

sub collapse {
  warn "Collapsing $_[0]...\n" if $debug & $debug_flow;
  local($i,$ii,$_)=(shift);
  if (($ii=$#chunks-$level[$#level]+1)<$i) {
    warn "Too few chunks ($ii) in inner level, expecting $i";
    $i=$ii;
  }
  if ($i>0) {
    for (0..$i-1) {
      &collapseOne($#chunks-$_);
    }
    for (1..$i-1) {
      $chunks[$#chunks-$_+1]=$chunks[$#chunks-$i+1]+$i-$_;
    }
  }
}

# Collapses all the chunks on given level

sub collapseAll {&collapse($#chunks-$level[$#level]+1);}

# Collapses a given chunk in the array @out. No correction of @chunks is
# performed

sub collapseOne {
  local($n)=(shift);
  local($out,$last,$_)=($out[$chunks[$n]]);
  if ($n==$#chunks) {$last=$#out;} else {$last=$chunks[$n+1]-1;}
  warn "Collapsing_one $n, records $chunks[$n]..$last\n"
    if $debug & $debug_flow;
  return unless $last>$chunks[$n];
  warn "Collapsing chunk $n beginning at $chunks[$n], ending at $last\n" if $debug & $debug_flow;
  for ($chunks[$n]+1..$last) {
    $out=&join_records($out,$out[$_]);
  }
  splice(@out,$chunks[$n],$last+1-$chunks[$n],$out);
  warn "Collapsed $chunks[$n]: $out[$chunks[$n]]\n__END__\n" if $debug & $debug_record;
}

# Deletes extra spaces at the end of a record

sub trim_end {
  local($h,$str)=(split(/,/,$_[0],5))[0,4];
  if (!$h) {
    $str =~ s/\s+$//;
    $_[0]=&string2record($str);
    warn "Trimmed End `$_[0]'\n__END__\n" if $debug & $debug_record;
  }
}

# Deletes extra spaces at the beginning of a record

sub trim_beg {
  local($h,$str)=(split(/,/,$_[0],5))[0,4];
  if (!$h) {
    $str =~ s/^\s+//;
    $_[0]=&string2record($str);
    warn "Trimmed Beg `$_[0]'\n__END__\n" if $debug & $debug_record;
  }
}

# Deletes extra spaces at the ends of a chunk with given number

sub trim_one {
  &trim_beg($out[$chunks[$_[0]]]);
  &trim_end($_[0]==$#chunks? $out[$#out]: $out[$chunks[$_[0]+1]-1]);
}

# Deletes extra spaces at the ends of a given number of chunks

sub trim {
  for ($#chunks-$_[0]+1..$#chunks) {&trim_one($_);}
}

1;
