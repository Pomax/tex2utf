package TeXHandlers;

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
  f_subSuper f_superSub f_subscript f_superscript f_radical f_fraction
  f_choose f_buildrel f_overline f_underline f_not f_putunder f_putover
  f_putpar f_putover_string f_widehat f_widetilde f_get1 f_begin f_end
  f_literal_no_length f_discard f_left f_leftright f_leftright_go
  f_arrow f_arrow_v sup_sub
);

# Takes the last two records, returns a record that contains them and forms
# SupSub block

sub f_subSuper {
  warn "Entering f_subSuper...\n" if $debug & $debug_flow;
  trim(2);
  collapse(2);
  assertHave(2) || finish("",1);
  &sup_sub(0,1);
}

sub sup_sub {
  local($p1,$p2)=($#out-shift,$#out-shift);
  warn "Super $p1 $out[$p1]\nSub $p2 $out[$p2]\n__END__\n" if $debug & $debug_record;
  local($h1,$l1,$b1,$sp1,$str1)=split(/,/,$out[$p1],5);
  local($h2,$l2,$b2,$sp2,$str2)=split(/,/,$out[$p2],5);
  if ($l1==0 && $l2==0) {return;}
  $h1 || $h1++;
  $h2 || $h2++;
  local($h,$l)=($h1+$h2+1, ($l1>$l2 ? $l1: $l2));
  $#chunks--;
  $#out--;
  if ($l1==0) {
    $h2++;
    $out[$#out]="$h2,$l,0,0,\n$str2";
  } elsif ($l2==0) {
    $h=$h1+1;
    $out[$#out]="$h,$l,$h1,0,$str1\n";
  } else {
    $out[$#out]="$h,$l,$h1,0,$str1\n\n$str2";
  }
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(2,1);
}

# Takes the last two records, returns a record that contains them and forms
# SupSub block

sub f_superSub {
  warn "Entering f_superSub...\n" if $debug & $debug_flow;
  trim(2);
  collapse(2);
  assertHave(2) || finish("",1);
  &sup_sub(1,0);
}

sub f_subscript {
  $wait[$#level]=2;
  $action[$#level]="f_subSuper";
  if (($Parser::par !~ s/^\s*\^//) &&
      ($Parser::par !~ s:^\s*\\begin\s*\{Sp\}:\\begin\{matrix\}:)) {
    commit(&empty);
  }
}

sub f_superscript {
  $wait[$#level]=2;
  $action[$#level]="f_superSub";
  if (($Parser::par !~ s/^\s*\_//) &&
      ($Parser::par !~ s:^\s*\\begin\s*\{Sb\}:\\begin\{matrix\}:)) {
    commit(&empty);
  }
}

# digest \begin{...} and similar: handles argument to a subroutine
# given as argument

sub f_get1 {
  warn "Entering f_get1...\n" if $debug & $debug_flow;
  (warn "Argument of f_get1 consists of 2 or more chunks", return)
      if $#out != $chunks[$#chunks];
  local($rec,$sub);
  $rec=$out[$#out];
  $rec=~s/.*,//;
  $sub=shift;
  defined $sub ? return &$sub($rec): return $rec;
}

sub f_begin {
  warn "Entering f_begin...\n" if $debug & $debug_flow;
  collapse(1);
  assertHave(1) || finish("");
  local($arg,$env)=(&f_get1());
  finish_ignore(1);
  $arg=~s/^\s+//;
  $arg=~s/\s+$//;
  return if defined $environment_none{$arg};
  if (defined ($env=$environment{$arg})) {
    local($b,$e)=split(/,/,$env);
    for (split(":",$b)) {&callsub($_);}
  } else {
    require Parser;
    Parser::puts("\\begin{$arg}");
  }
}

sub f_end {
  warn "Entering f_end...\n" if $debug & $debug_flow;
  collapse(1);
  assertHave(1) || finish("");
  local($arg,$env)=(&f_get1());
  finish_ignore(1);
  $arg=~s/^\s+//;
  $arg=~s/\s+$//;
  return if defined $environment_none{$arg};
  if (defined ($env=$environment{$arg})) {
    local($b,$e)=split(/,/,$env,2);
    for (split(":",$e)) {&callsub($_);}
  } else {
    require Parser;
    Parser::puts("\\end{$arg}");
  }
}

sub f_literal_no_length {
  warn "Entering f_literal_with_length...\n" if $debug & $debug_flow;
  collapse(1);
  assertHave(1) || finish("",1);
  record_forcelength($out[$#out], 0);
  finish(1,1);
}

sub f_discard {
  warn "Entering f_discard...\n" if $debug & $debug_flow;
  finish_ignore($wait[$#level]);
}

# Takes the last record, returns a record that contains it and forms
# radical block

sub f_radical {
  warn "Entering f_radical...\n" if $debug & $debug_flow;
  trim(1);
  collapse(1);
  assertHave(1) || finish("",1);
  warn "Radical of $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($h,$l,$b)=($out[$#out] =~ /^(\d+),(\d+),(\d+)/g);
  $h || $h++;
  local($out,$b1,$h1);
  $out=&vStack(&string2record(("─" x $l)."┐" ),$out[$#out]);
  $b1=$b+1;
  $h1=$h+1;
  &setbaseline($out,$b1);
  $out[$#out]=&join_records("$h1,2,$b1,0, ┌\n" . (" │\n" x ($h-1)) . '⟍│',$out);
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(1,1);
}

# Takes the last two records, returns a record that contains them and forms
# fraction block

sub f_fraction {
  warn "Entering f_fraction...\n" if $debug & $debug_flow;
  trim(2);
  collapse(2);
  assertHave(2) || finish("",1);
  warn "Numer `$out[$#out-1]'\nDenom `$out[$#out]'\n__END__\n" if $debug & $debug_record;
  local($l1,$l2)=(&get_length($out[$#out-1]),&get_length($out[$#out]));
  local($len)=(($l1>$l2 ? $l1: $l2));
  $out[$#out-1]=&vStack(&vStack(&center($len,$out[$#out-1]),
                         &string2record("─" x $len)),
                 &center($len,$out[$#out]));
  $#chunks--;
  $#out--;
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(2,1);
}

sub f_choose {
  warn "Entering f_choose...\n" if $debug & $debug_flow;
  trim(2);
  collapse(2);
  assertHave(2) || finish("",1);
  warn "Numer `$out[$#out-1]'\nDenom `$out[$#out]'\n__END__\n" if $debug & $debug_record;
  local($l1,$l2)=(&get_length($out[$#out-1]),&get_length($out[$#out]));
  local($len)=(($l1>$l2 ? $l1: $l2));
  $out[$#out]=&vStack(&vStack(&center($len,$out[$#out-1]),
                         &string2record(" " x $len)),
                 &center($len,$out[$#out]));
  $#chunks++;
  $#out++;
  $out[$#out - 2] = &string2record("(");
  $out[$#out] = &string2record(")");
  local($h,$b)=($out[$#out-1] =~ /^(\d+),\d+,(\d+)/)[0,1];
  &makehigh($out[$#out-2],$h,$b,0,1);
  &makehigh($out[$#out],$h,$b,1,0);
  finish(2,1);
}

sub f_buildrel {
  warn "Entering f_buildrel...\n" if $debug & $debug_flow;
  trim(3);
  collapse(3);
  assertHave(3) || finish("",1);
  warn "What: $out[$#out-2]\nOver $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($rec)=($out[$#out-2]);
  $out[$#out-2]=$out[$#out];
  $#chunks-=2;
  $#out-=2;
  &f_putover($rec,1);
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(3,1);
}

sub f_overline {
  warn "Entering f_overline...\n" if $debug & $debug_flow;
  trim(1);
  collapse(1);
  assertHave(1) || finish("",1);
  warn "Overlining $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($h,$len,$b)=($out[$#out] =~ /^(\d+),(\d+),(\d+)/);
  $out[$#out]=&vStack(&string2record("_" x $len),
                      $out[$#out]);
  $b++;
  &setbaseline($out[$#out],$b);
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(1,1);
}

sub f_underline {
  warn "Entering f_underline...\n" if $debug & $debug_flow;
  trim(1);
  collapse(1);
  assertHave(1) || finish("",1);
  warn "Underlining $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($h,$len,$b)=($out[$#out] =~ /^(\d+),(\d+),(\d+)/);
  $out[$#out]=&vStack($out[$#out],&string2record("_" x $len));
  &setbaseline($out[$#out],$b);
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(1,1);
}

sub f_not {
  warn "Entering f_not...\n" if $debug & $debug_flow;
  collapse(1);
  assertHave(1) || finish("",1);
  warn "Negating $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($str)=(split(/,/,$out[$#out]))[4];
  if ($str eq "=") {
    $out[$#out]=$contents{"\\neq"};
  } elsif ($str =~ /^\s*\|\s*$/) {
    $out[$#out]=$contents{"\\nmid"};
  } elsif ($out[$#out] eq $contents{"\\in"}) {
    $out[$#out]=$contents{"\\notin"};
  } else {
    $out[$#out]=&join_records(&string2record("\\not"),$out[$#out]);
  }
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(1,1);
}

sub f_putunder {
  warn "Entering f_putunder...\n" if $debug & $debug_flow;
  trim(1);
  collapse(1);
  assertHave(1) || finish("",1);
  warn "Putting Under $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($h,$len,$b)=($out[$#out] =~ /^(\d+),(\d+),(\d+)/);
  local($l2)=(&get_length($_[0]));
  local($len)=(($l1>$l2 ? $l1: $l2));
  $out[$#out]=&vStack(&center($len,$out[$#out]),&center($len,shift));
  &setbaseline($out[$#out],$b);
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(1,1);
}

# if has additional true argument will not finish
# Takes record to put over

sub f_putover {
  warn "Entering f_putover...\n" if $debug & $debug_flow;
  trim(1);
  collapse(1);
  assertHave(1) || finish("",1);
  warn "Putting Over $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($h,$l1,$b,$b1)=($out[$#out] =~ /^(\d+),(\d+),(\d+)/);
  local($l2)=(&get_length($_[0]));
  local($len)=(($l1>$l2 ? $l1: $l2));
  ($b1)=($_[0] =~ /^(\d+)/);
  $b+=$b1+1;
  $out[$#out]=&vStack(&center($len,shift),&center($len,$out[$#out]));
  &setbaseline($out[$#out],$b);
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(1,1) unless shift;
}

sub f_putpar {
  warn "Entering f_putpar...\n" if $debug & $debug_flow;
  trim(1);
  local($l,$r)=split(";",shift);
  collapse(1);
  assertHave(1) || finish("",1);
  warn "Putting Parentheses $out[$#out]\n__END__\n" if $debug & $debug_record;
  $out[$#out]=&join_records(&string2record($l),
      &join_records($out[$#out],&string2record($r)));
  finish(1,1);
}

sub f_putover_string {
  &f_putover(&string2record);
}

sub f_widehat {
  trim(1);
  collapse(1);
  local($l)=(&get_length($out[$#out]));
  if ($l<=1) {&f_putover(&string2record("^"));}
  else {&f_putover(&string2record("/" . "~" x ($l-2) . "\\"));}
}

sub f_widetilde {
  trim(1);
  collapse(1);
  local($l,$l1)=(&get_length($out[$#out]));
  if ($l<=1) {&f_putover(&string2record("~"));}
  elsif ($l<=3) {&f_putover(&string2record("/\\/"));}
  else {&f_putover(&string2record("/" . "~" x ($l1=int($l/2-1)) .
     "\\" . "_" x ($l-3-$l1) . "/"));}
}

sub f_left {
  trim(1);
  collapse(1);
  finish(1);
  LevelManager::start("LeftRight");
}

sub f_leftright_go {
  trim(1);
  collapse(1);
  local($l,$r)=split(";",shift);
  assertHave(1) || warn "Left-Right not balanced";
  local($rec)=($out[$#out]);
  $#out--;
  $wait[$#level]="junk";
  LevelManager::start(3,"f_leftright");
  require Parser;
  Parser::puts($l);
  commit($rec);
  Parser::puts($r);
  finish("junk");
}

sub f_leftright {
  trim(1);
  collapse(1);
  assertHave(3) || warn "Left-Right not balanced";
  local($h,$b)=($out[$#out-1] =~ /^(\d+),\d+,(\d+)/)[0,1];
  &makehigh($out[$#out-2],$h,$b,0,1);
  &makehigh($out[$#out],$h,$b,1,0);
  finish(3);
}

# takes two tips of arrow as argument separated by ";",
# we assume that total length is 1

sub f_arrow {
  warn "Entering f_arrow...\n" if $debug & $debug_flow;
  local($l,$r)=split(";",shift);
  trim(2);
  collapse(2);
  assertHave(2) || finish("",1);
  warn "Over: $out[$#out-1]\nUnder: $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($l1,$l2)=(&get_length($out[$#out-1]),&get_length($out[$#out]));
  local($len)=(($l1>$l2 ? $l1: $l2));
  $out[$#out-1]=&vStack(&vStack(&center($len+4,$out[$#out-1]),
                         &string2record(" $l" ."-" x ($len+1) . "$r ")),
                 &center($len+4,$out[$#out]));
  $#chunks--;
  $#out--;
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(2,1);
}

# takes two tips of arrow as argument separated by ";",
# we assume that total length is 1

sub f_arrow_v {
  warn "Entering f_arrow_v...\n" if $debug & $debug_flow;
  local($l,$r)=split(";",shift);
  trim(2);
  collapse(2);
  assertHave(2) || finish("",1);
  warn "Over: $out[$#out-1]\nUnder: $out[$#out]\n__END__\n" if $debug & $debug_record;
  local($h1,$b1)=($out[$#out-1] =~ /^(\d+),\d+,(\d+)/);
  local($h2,$b2)=($out[$#out] =~ /^(\d+),\d+,(\d+)/);
  local($b)=(($b1>$b2 ? $b1: $b2));
  local($res)=(&join_records($out[$#out-1],$out[$#out]));
  local($h,$bb)=($res =~ /^(\d+),\d+,(\d+)/);
  $bb=$b+1;
  $out[$#out-1]=&vStack(&vputs(" " x ($b-$b1+1)),
                        $out[$#out-1]);
  &setbaseline($out[$#out-1],$bb);
  $out[$#out]=&vStack(&vputs(" " x ($b-$b2+1)),
                                     $out[$#out]);
  &setbaseline($out[$#out],$bb);
  $out[$#out-1]=&join_records(&join_records($out[$#out-1],
                         &vputs($l ."|" x ($h+1) . $r,$b+1)),
                      $out[$#out]);
  $#chunks--;
  $#out--;
  warn "a:Last $#chunks, the first on the last level=$#level is $level[$#level]" if $debug & $debug_flow;
  finish(2,1);
}

1;
