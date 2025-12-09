package Parser;

use strict;
use warnings;
no strict 'vars';  # Allow old-style local variables
no strict 'refs';  # Allow symbolic references for function calls
use utf8;
use Tex2UtfConfig;
use Records;
use OutputBuffer;
use LevelManager;
use MacroExpansion;
use TeXHandlers;
use MatrixHandler;

use Exporter 'import';
our @EXPORT = qw(
  $par paragraph subscript superscript dollar ddollar open_curly close_curly
  ampersand at item bbackslash noindent over choose left right beg_lr puts par
);

# Current paragraph being parsed
our $par;

# ===========================================
#
#   Main script entry point: this function
#  runs over and over until there is nothing
#         left for it to process.
#
# ===========================================
sub paragraph {
  $par=<>; # load stdio input into $par
  return 0 unless defined $par;
  return 1 unless $par =~ /\S/; # whitespace only

  # TEX2UTF Edit: remove everything before "\begin{document}"
  $par =~ s/^[\w\W]*(\\begin\{document\})/$1/g;

  print "\n" if $secondtime++ && !$opt_by_par;
  $par =~ s/((^|[^\\])(\\\\)*)(%.*\n[ \t]*)+/$1/g;
  $par =~ s/\n\s*\n/\\par /g;
  $par =~ s/\s+/ /g;
  $par =~ s/\s+$//;
  $par =~ s/(\$\$)\s+/$1/g;
  $par =~ s/\\par\s*$//;

  local($defcount,$piece,$pure,$type,$sub,@t,$arg)=(0);

  &commit("1,5,0,0,     ")
    unless $opt_noindent || ($par =~ s/^\s*\\noindent\s*([^a-zA-Z\s]|$)/$1/);
  while ($tokenByToken[$#level] ?
      ($par =~ s/^\s*($tokenpattern)//o): ($par =~ s/^($multitokenpattern)//o)) {
    warn "tokenByToken=$tokenByToken[$#level], eaten=`$1'\n"
        if $debug & $debug_parsing;
    if (($piece=$1) =~ /^$usualtokenclass/o) {
      # plain piece
      &puts($piece);
    } else {
      # macro or delimiter
      ($pure = $piece) =~ s/\s+$//;
      if (defined ($type=$MacroExpansion::type{$pure})) {
        if ($type eq "def") {
          warn "To many def expansions in a paragraph" if $defcount++==$maxdef;
          last if $defcount>$maxdef;
          @t=(0);
          for (1..$MacroExpansion::args{$pure}) {
            push(@t,&get_balanced());
          }
          warn "Defined token `$pure' found with $MacroExpansion::args{$pure} arguments @t[1..$#t]\n"
          if $debug & $debug_parsing;
          $sub=$MacroExpansion::def{$pure};
          $sub =~ s/(^|[^\\#])#(\d)/$1 . $t[$2]/ge if $MacroExpansion::args{$pure};
          $par=$sub . $par;
        } elsif ($type eq "sub") {
          $sub=$MacroExpansion::contents{$pure};
          index($sub,";")>=0 ? (($sub,$arg)=split(";",$sub,2), &$sub($pure,$arg)) : &$sub($pure);
        } elsif ($type =~ /^sub(\d+)$/) {
          LevelManager::start($1,"f_$MacroExpansion::contents{$pure}");
          $tokenByToken[$#level]=1;
        } elsif ($type =~ /^get(\d+)$/) {
          LevelManager::start($1+1);
          &puts($piece);
          $tokenByToken[$#level]=1;
        } elsif ($type =~ /^discard(\d+)$/) {
          LevelManager::start($1,"f_discard");
          $tokenByToken[$#level]=1;
        } elsif ($type eq "record") {
          &commit($MacroExpansion::contents{$pure});
        } elsif ($type eq "self") {
          &puts(substr($pure,1) . ($pure =~ /^\\[a-zA-Z]/ ? " ": ""));
        } elsif ($type eq "par_self") {
          &finishBuffer;
          &commit("1,5,0,0,     ");
          &puts($pure . ($pure =~ /^\\[a-zA-Z]/ ? " ": ""));
        } elsif ($type eq "self_par") {
          &puts($pure . ($pure =~ /^\\[a-zA-Z]/ ? " ": ""));
          &finishBuffer;
          &commit("1,5,0,0,     ")
          unless $par =~ s/^\s*\\noindent(\s+|([^a-zA-Z\s])|$)/$2/;
        } elsif ($type eq "string") {
          &puts($MacroExpansion::contents{$pure},1);
        } elsif ($type eq "nothing") {
        } else {
          warn "Error with type `$type' while interpreting `$pure'";
        }
      } else {
        &puts($piece);
      }
    }
  }
  warn "Unrecognized part of input `$par',\n\ttoken-by-token[$#level]=$tokenByToken[$#level]" if $par ne "";

  &finishBuffer if $#out >= 0;

  1;
}

sub subscript {
  LevelManager::start(1,"f_subscript");
  $tokenByToken[$#level]=1;
}

sub superscript {
  LevelManager::start(1,"f_superscript");
  $tokenByToken[$#level]=1;
}

# ==========================
# Start of inline mode maths
# ==========================
sub dollar {
  if ($wait[$#level] eq '$') {
    trim_end($out[$#out]);
    LevelManager::finish('$');
  }
  else {
    LevelManager::start('$');
    $par =~ s/^\s+//;
  }
}

# ==========================
# Start of block mode maths
# ==========================
sub ddollar {
  if (defined $wait[$#level] && $wait[$#level] eq '$$') {
    trim_end($out[$#out]);
    LevelManager::finish('$$');
    return unless $#out>=0;
    $#chunks=0;
    $chunks[0]=0;
    trim(1);
    collapse(1);
    &printrecord(&center($linelength,$out[0]));
    @level=(0);
    @chunks=(0);
    @tokenByToken=(0);
    @out=();
    $curlength=0;
  }
  else {
    &finishBuffer;
    LevelManager::start('$$');
  }
  $par =~ s/^\s+//;
}

sub item {
  &finishBuffer;
  # To make unexpandable:
  &commit("1,11,0,0,     (\@)   ");
}

sub bbackslash {
  if ($wait[$#level] eq '$$') {
    &ddollar();
    &ddollar();
  } elsif ($wait[$#level] eq 'endCell') {
    return if $par =~ /^\s*\\end/; # Ignore the last one
    LevelManager::finish('endCell', 1);
    trim(1);
    collapse(1);
    LevelManager::finish('endRow', 1);
    LevelManager::start('endRow');
    LevelManager::start('endCell');
  } else {
    &par;
  }
}

sub ampersand {
  if ($wait[$#level] eq 'endCell') {
    LevelManager::finish('endCell',1);
    trim(1);
    collapse(1);
    LevelManager::start('endCell');
  }
}

sub open_curly {
  LevelManager::start("}");
}

sub close_curly {
  LevelManager::finish("}");
}

sub at {
  local($c,$first,$second,$t,$m)=($par =~ /^(.)/);
  if ($c eq '@') {&puts('@');$par =~ s/^.//;}
  elsif (index("<>AV",$c)>=0) {
    $m="&" if ($wait[$#level] eq 'endCell');
    $m="&&" if $m eq "&" && index("AV",$c)>=0;
    &ampersand if $m eq "&";
    $par =~ s/^.//;
    $first=$second="";
    while (($t=&get_balanced()) ne $c && defined $t) {
      $first .= $t;
    }
    while (($t=&get_balanced()) ne $c && defined $t) {
      $second .= $t;
    }
    $par="{$first}{$second}$m" . $par;
    local($l,$r);
    ($l=$c) =~ tr/A>V/^/d;
    ($r=$c) =~ tr/<A//d;
    index("<>",$c)>=0 ?
       LevelManager::start(2,"f_arrow;$l;$r"):
       LevelManager::start(2,"f_arrow_v;$l;$r");
  }
  elsif ($c eq "." && $wait[$#level] eq 'endCell') {
    &ampersand;
    &ampersand;
    $par =~ s/^.//;
  }
  else {&puts('@');}
}

sub noindent {
  if ($#out == 0 && $#chunks == 0 && $out[$#out] eq '1,5,0,0,     ') {
    $#out--;
    $#chunks--;
  } else {
    &puts('\\noindent');
  }
}

sub choose {
  if ($wait[$#level] eq '}') {
    local($prevw)=($wait[$#level-1]);
    $wait[$#level-1]="junk";
    LevelManager::finish("}", 1);
    collapse(1);
    assertHave(1) || LevelManager::finish("",1);
    local($rec)=$out[$#out];
    $#out--;
    $#chunks--;
    LevelManager::start(2,"f_choose");
    $wait[$#level-1]=$prevw;
    LevelManager::start("}");
    &commit($rec);
    LevelManager::finish("}",1);
    LevelManager::start("}");
  } else {&puts("\\choose");}
}

sub over {
  if ($wait[$#level] eq '}') {
    local($prevw)=($wait[$#level-1]);
    $wait[$#level-1]="junk";
    LevelManager::finish("}", 1);
    collapse(1);
    assertHave(1) || LevelManager::finish("",1);
    local($rec)=$out[$#out];
    $#out--;
    $#chunks--;
    LevelManager::start(2,"f_fraction");
    $wait[$#level-1]=$prevw;
    LevelManager::start("}");
    &commit($rec);
    LevelManager::finish("}",1);
    LevelManager::start("}");
  } else {&puts("\\over");}
}

sub left {
  LevelManager::start(3,"f_leftright");
  $tokenByToken[$#level]=1;
  LevelManager::start(1,"f_left");
  $tokenByToken[$#level]=1;
}

sub right {
  LevelManager::finish("LeftRight",1);
  trim(1);
  collapse(1);
}

sub beg_lr {
  LevelManager::start(1,"f_leftright_go" . ";" . shift);
  $tokenByToken[$#level]=1;
}

# Commits a given string

sub puts {
  &commit(&string2record);
}

sub par {
  &finishBuffer;
  &commit("1,5,0,0,     ")
    unless $par =~ s/^\s*\\noindent\s*(\s+|([^a-zA-Z\s])|$)/$2/;
}

1;
