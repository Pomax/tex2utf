package Records;

use strict;
use warnings;
no strict 'vars';  # Allow old-style local variables
use utf8;
use Tex2UtfConfig;

use Exporter 'import';
our @EXPORT = qw(
  debug_print_record cut printrecord join_records get_length get_height
  setbaseline empty string2record record_forcelength vStack superSub
  subSuper center vputs makehigh makecompound
);

# Format of the record: height,length,baseline,expandable-spaces,string
# The string is not terminated by \n, but separated into rows by \n.
# height=0 denotes expandable string
# Baseline=3 means the 4th row is the baseline

sub debug_print_record {
  local($h,$l,$b,$xs,$s) = split /,/, shift, 5;
  local(@arr) = split /\n/, $s;
  print STDERR "len=$l, h=$h, b=$b, exp_sp=$xs.\n";
  local($i) = 0;
  for (@arr) {
    local($lead) = ($i++ == $b) ? 'b [' : '  [';
    print STDERR "$lead$_]\n";
  }
  while ($i < $h) { # Empty lines may skipped
    local($lead) = ($i++ == $b) ? 'b' : '';
    print STDERR "$lead\n";
  }
}

# Takes length and a record, returns 2 records

sub cut {
  local($length)=(shift);
  local($h,$l,$b,$sp,$str)=split(/,/,shift,5);
  local($st1,$st2)=("","");
  local($sp1,$sp2,$first,$l2)=(0,0,1,$l-$length);
  return (shift,&empty) if $l2<0;
  if ($h) {
    for (split(/\n/,$str,$h)) {
      if (!$first) {
        $st1 .= "\n";
        $st2 .= "\n";
      } else {$first=0;}
      $st1 .= substr($_,0,$length);
      $st2 .= substr($_,$length);
    }
  } else {
    $st1 = substr($str,0,$length);
    $st2 = substr($str,$length);
  }
  return ("$h,$length,$b,$sp1,$st1","$h,$l2,$b,$sp2,$st2");
}

# Outputs a record

sub printrecord {
  warn "Printing $_[0]\n__ENDPRINT__\n" if $debug & $debug_record;
  local($h,$l,$b,$sp,$str)=split(/,/,shift,5);
  print $str,"\n";
}

# Joins two records

sub join_records {
  local($h1,$l1,$b1,$sp1,$str1)=split(/,/,shift,5);
  local($h2,$l2,$b2,$sp2,$str2)=split(/,/,shift,5);
  $h1 || $h1++;
  $h2 || $h2++;
  local($h,$l,$b,$sp,$str,@str,@str2)=(0,0,0,$sp1+$sp2,"");
  $b = $b1 > $b2 ? $b1 : $b2;
  # Calculate space below baseline
  $h = $h1-$b1 > $h2-$b2 ? $h1-$b1 : $h2-$b2;
  # And height
  $h += $b;
  $l=$l1+$l2;
  @str="" x $h;
  @str[$b-$b1 .. $b-$b1+$h1-1]=split(/\n/,$str1,$h1);
  @str2[0..$h2-1]=split(/\n/,$str2,$h2);
  unless (length($str2[$b2])) {
    $str2[$b2] = ' ' x $l2; # Needed for length=0 "color" strings in the baseline.
  }
  if ($debug & $debug_record && (grep(/\n/,@str) || grep(/\n/,@str2))) {
    warn "\\n found in \@str or \@str2";
    warn "`$str1', need $h1 rows\n";
    warn "`$str2', need $h2 rows\n";
  }
  for (0..$h2-1) {
    my $idx = $b-$b2+$_;
    $str[$idx] = '' unless defined $str[$idx];
    $str[$idx] .= " " x ($l1 - length ($str[$idx])) . $str2[$_];
  }
  return "$h,$l,$b,$sp," . join("\n",@str);
}

# Gets a length of a record

sub get_length {
  (warn "Wrong format of a record `$_[0]'", return 0)
      unless $_[0] =~ /^\d+,(\d+)/;
  $1;
}

# Gets a height of a record

sub get_height {
  (warn "Wrong format of a record `$_[0]'", return 0)
      unless $_[0] =~ /^(\d+),/;
  $1;
}

# Sets baseline of a record, Usage s...(rec,base)

sub setbaseline {
  (warn("Wrong format of a record `$_[0]'"), return undef)
      unless $_[0] =~ s/^(\d+,\d+,)(\d+)/$1$_[1]/;
}

# Return an empty record

sub empty {
  return "0,0,0,0,";
}

# Additional argument specifies if to make not-expandable, not-trimmable

sub string2record {
  local($h,$sp)=(0);
  if ($_[1]) {$h=1;$sp=0;}
  else {
    $sp=($_[0] =~ /(\s)/g);
    $sp || ($sp=0); # Sometimes it is undef?
  }
  return "$h," . length($_[0]) . ",0,$sp,$_[0]";
}

# The second argument forces the block length no matter what is the
# length the string (for strings with screen escapes).

sub record_forcelength {
  $_[0] =~ s/^(\d+),(\d+)/$1,$_[1]/;
}

# Takes two records, returns a record that concatenates them vertically
# To make fraction simpler, baseline is the last line of the first record

sub vStack {
  local($h1,$l1,$b1,$sp1,$str1)=split(/,/,shift,5);
  local($h2,$l2,$b2,$sp2,$str2)=split(/,/,shift,5);
  $h1 || $h1++;
  $h2 || $h2++;
  local($h,$l,$b)=($h1+$h2, ($l1>$l2 ? $l1: $l2), $h1-1);
  warn "\$h1=$h1, \$h2=$h2, Vstacked: $h,$l,$b,0,$str1\n$str2\n__END__\n" if $debug & $debug_record;
  return "$h,$l,$b,0,$str1\n$str2";
}

# Takes two records, returns a record that contains them and forms
# SupSub block

sub superSub {
  local($h1,$l1,$b1,$sp1,$str1)=split(/,/,shift,5);
  local($h2,$l2,$b2,$sp2,$str2)=split(/,/,shift,5);
  $h1 || $h1++;
  $h2 || $h2++;
  local($h,$l)=($h1+$h2+1, ($l1>$l2 ? $l1: $l2));
  return "$h,$l,$h1,0,$str1\n\n$str2";
}

# Takes two records, returns a record that contains them and forms
# SupSub block

sub subSuper {
  local($h1,$l1,$b1,$sp1,$str1)=split(/,/,shift,5);
  local($h2,$l2,$b2,$sp2,$str2)=split(/,/,shift,5);
  $h1 || $h1++;
  $h2 || $h2++;
  local($h,$l)=($h1+$h2+1, ($l1>$l2 ? $l1: $l2));
  return "$h,$l,$h1,0,$str2\n\n$str1";
}

# Takes a number and a record, returns a centered record

sub center {
  local($len,$left)=(shift,0);
  warn "Entering center, ll=$len, rec=$_[0]\n__ENDREC__\n" if $debug & $debug_flow;
  local($h1,$l1,$b1,$sp1,$str1)=split(/,/,$_[0],5);
  $h1 || $h1++;
  if (($left=$len-$l1)<=0) {return $_[0];}
  $left=int($left/2);
  local($out,$first)=("",1);
  for (split(/\n/,$str1,$h1)) {
    if ($first) {$first=0;}
    else {$out .= "\n";}
    $out .= " " x $left . $_;
  }
  return "$h1,$len,$b1,0,$out";
}

# put strings vertically, returns a record with the second argument as baseline

sub vputs {
  local($b)=($_[1]);
  $b=0 unless defined $b;
  return length($_[0]) . ",1,$b,0," . join("\n",split('',$_[0]));
}

# Takes a record, height, baseline, spaces_toleft and _toright
# and makes this record this high

sub makehigh {
  local($str)=(split(",",$_[0],5))[4];
  local($h,$b,$d)=($_[1],$_[2]+1);
  warn "Entering makehigh(@_)\n" if $debug & $debug_flow;
  if ($str eq ".") {$_[0] =~ s/\.$/ /;return;}
  $h=1 unless $h;
  $d=$h-$b;
  return if $h<2 || $h==2 && index("()<>",$str)>=0;
  local(@c);
  # split pattern:
  #  0: base string
  #  1: oneside expander
  #  2: real expander
  #  3: top tip
  #  4: bottom top
  #  5: mid
  if    ($str eq "(") {@c=split(":",'(: :│:╭:╰:│');}
  elsif ($str eq ")") {@c=split(":",'): :│:╮:╯:│');}
  elsif ($str eq "{") {@c=split(":",'{: :│:╭:╰:╡');}
  elsif ($str eq "}") {@c=split(":",'}: :│:╮:╯:╞');}
  elsif ($str eq "|" && $str eq "||")
                      {@c=split(":",'|:|:|:|:|:|');}
  elsif ($str eq "[") {@c=split(":",'[: :│:┌:└:│');}
  elsif ($str eq "]") {@c=split(":",']: :│:┐:┘:│');}
  elsif ($str eq "<" || $str eq ">") {
    return if $h==2;
    local($l)=($b);
    $l = $d+1 if $b < $d+1;
    for (2..$l) {
      $_[0]=&join_records($_[0], &vputs("⧸" . " " x (2*$_-3) . "⧹",$_-1)) if $str eq "<";
      $_[0]=&join_records(&vputs("⧹" . " " x (2*$_-3) . "⧸",$_-1), $_[0]) if $str eq ">";
    }
    if ($str eq "<") {
      $_[0] = &join_records($_[0], &string2record(" "));
      $_[0] =~ s/< / ⟨/;
    }
    elsif ($str eq ">") {
      $_[0]=&join_records(&string2record(" "), $_[0]);
      $_[0] =~ s/>/⟩/;
    }
    return;
  }
  else {return;}

  # form initial typesetting
  $_[0]=&vputs(&makecompound($b,$d,@c), $b-1);

  # pad out the shape with spaces
  $_[0]=&join_records($_[0],$_[0]) if length($str)==2;
  $_[0]=&join_records(&string2record(" " x $_[3]),$_[0]) if $_[3];
  $_[0]=&join_records($_[0],&string2record(" " x $_[4])) if $_[4];
}

# Arguments from $b/$d:
#
#  0: ascent (number)
#  1: descent (number)
#
# Arguments from @c:
#
#  2: base string
#  3: oneside expander
#  4: real expander
#  5: top tip
#  6: bottom top
#  7: mid
#
# All component should be one character long
sub makecompound {
  $ascent = $_[0];
  $descent = $_[1];

  $base = $_[2];
  $exp_one_side = $_[3];
  $exp_real = $_[4];
  $top = $_[5];
  $bottom = $_[6];
  $middle = $_[7];

  if ($ascent >= 1 && $descent > 0 && $exp_real eq $middle) {
    return $top . $exp_real x ($ascent + $descent - 2) . $bottom;
  }

  # No descent:
  if ($descent <= 0) {
    return $exp_one_side x ($ascent - 1) . $base;
  }

  # No ascent:
  if ($ascent <= 1) {
    return $base . $exp_one_side x ($descent - 0);
  }

  $above = ($ascent >= 2) ? $top . $exp_real x ($ascent - 2) : $top;
  $below = ($descent > 1) ? $exp_real x ($descent - 1) . $bottom : $bottom;
  return $above . $middle . $below;
}

1;
