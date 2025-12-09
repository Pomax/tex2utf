package MacroExpansion;

use strict;
use warnings;
no strict 'vars';  # Allow old-style local variables
no strict 'refs';  # Allow symbolic references
use utf8;
use Tex2UtfConfig;
use OutputBuffer;

use Exporter 'import';
our @EXPORT = qw(
  %type %contents %args %def %environment %environment_none @argStack
  callsub let let_exp def def_exp define defb get_balanced
);

# Type and content mappings
our %type = ();
our %contents = ();
our %args = ();
our %def = ();
our %environment = ();
our %environment_none = ();
our @argStack = ();

# Calls a subroutine, possibly with arguments

sub callsub {
  local($sub)=(shift);
  local($arg);
  if (index($sub,";")>=0) {
    ($sub,$arg)=split(";",$sub,2);
    # Try different namespaces for the function
    if (defined &{"TeXHandlers::$sub"}) {
      return &{"TeXHandlers::$sub"}($arg);
    } elsif (defined &{"Parser::$sub"}) {
      return &{"Parser::$sub"}($arg);
    } elsif (defined &{"MatrixHandler::$sub"}) {
      return &{"MatrixHandler::$sub"}($arg);
    } else {
      return &$sub($arg);
    }
  } else {
    # Try different namespaces for the function
    if (defined &{"TeXHandlers::$sub"}) {
      return &{"TeXHandlers::$sub"}();
    } elsif (defined &{"Parser::$sub"}) {
      return &{"Parser::$sub"}();
    } elsif (defined &{"MatrixHandler::$sub"}) {
      return &{"MatrixHandler::$sub"}();
    } else {
      return &$sub();
    }
  }
}

sub let {
  $Parser::par =~ s/^($tokenpattern)(= ?)?($tokenpattern)//o;
}

sub let_exp {
  $Parser::par =~ s/^($tokenpattern)(= ?)?($tokenpattern)//o;
  return if index($&,'@')>=0;
  local($what)=$1;
  $type{$what}='def';
  $& =~ /($tokenpattern)$/;
  $def{$what}=$1;
  $args{$what}=0;
  warn "Definition of `$what' with $args{$what} args is `$def{$what}'\n"
    if $debug & $debug_parsing;
}

sub def {
  $Parser::par =~ s/^[^{]*//;
  require LevelManager;
  LevelManager::start(1,"f_discard");
  $tokenByToken[$#level]=1;
}

sub def_exp {
  return unless $Parser::par =~ s:^(([^\\{]|\\.)*)\{:\{:;
  local($arg)=($1);
  local($def,$act)=(&get_balanced());
  return unless defined $def;
  return if index("$arg$def",'@')>=0;
  return if $def =~ /\\([egx]?def|fi)([^a-zA-Z]|$)/;
  $def .= " "  if $def =~ /($macro)$/o;
  &define($arg,$def);
}

# Arguments: Token . Parameters, Expansion

sub define {
  local($arg,$def,$act)=(shift,shift);
  return unless $arg =~ /^($active)/o;
  $act=$1;
  $args{$act}=$';
  return unless $args{$act} =~ /^(#\d)*$/;
  $args{$act}=length($args{$act})/2;
  $def{$act}=$def;
  $type{$act}='def';
  warn "Definition of `$act' with $args{$act} args is `$def'\n"
      if $debug & $debug_parsing;
}

sub defb {
  for (@_) {
    &define("\\$_","\\begin{$_}");&define("\\end$_","\\end{$_}");
  }
}

# Discards surrounding {}

sub get_balanced {
  return undef unless $Parser::par =~ s/^($tokenpattern)//;
  return $1 unless $1 eq '{';
  local($def,$lev)=('',1);
  while ($lev) {
    last unless $Parser::par =~ s/^[^\\{}]|\\.|[{}]//;
    $lev++ if $& eq '{';
    $lev-- if $& eq '}';
    $def .= $& if $lev;
  }
  (warn "Balanced text not finished!",return undef) if $lev;
  return $def;
}

sub arg2stack {push(@argStack,&get_balanced());}

1;
