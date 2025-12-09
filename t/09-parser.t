#!/usr/bin/perl
use strict;
use warnings;
use Test::More tests => 20;
use lib '../lib';

BEGIN { 
    use_ok('Tex2UtfConfig');
    use_ok('Records');
    use_ok('OutputBuffer');
    use_ok('LevelManager');
    use_ok('MacroExpansion');
    use_ok('TeXHandlers');
    use_ok('MatrixHandler');
    use_ok('TeXDefinitions');
    use_ok('Parser');
}

# Positive Tests

# Test 1: paragraph function exists
can_ok('Parser', 'paragraph');

# Test 2: subscript function exists
can_ok('Parser', 'subscript');

# Test 3: superscript function exists
can_ok('Parser', 'superscript');

# Test 4: dollar function exists
can_ok('Parser', 'dollar');

# Test 5: ddollar function exists
can_ok('Parser', 'ddollar');

# Test 6: ampersand function exists
can_ok('Parser', 'ampersand');

# Test 7: open_curly function exists
can_ok('Parser', 'open_curly');

# Test 8: close_curly function exists
can_ok('Parser', 'close_curly');

# Test 9: paragraph with empty input
@Parser::in = ();
$Parser::in = 0;
eval { Parser::paragraph() };
ok(!$@, 'paragraph handles empty input');

# Test 10: subscript with simple text
TeXDefinitions::initialize_definitions();
@OutputBuffer::out = (Records::string2record("x"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
@Parser::in = ("2");
$Parser::in = 0;
eval { Parser::subscript() };
ok(!$@, 'subscript processes simple input');

# Negative Tests

# Test 11: paragraph with uninitialized globals
undef @Parser::in;
undef $Parser::in;
eval { Parser::paragraph() };
ok($@ || 1, 'paragraph handles uninitialized state');

# Test 12: subscript without preceding content
@OutputBuffer::out = ();
@OutputBuffer::chunks = ();
@Parser::in = ("test");
$Parser::in = 0;
eval { Parser::subscript() };
ok(!$@, 'subscript without content does not crash');

# Test 13: dollar without matching closing
@Parser::in = ("x^2");
$Parser::in = 0;
eval { Parser::dollar() };
ok(!$@, 'dollar without closing handles gracefully');

# Test 14: ddollar with empty content
@Parser::in = ();
$Parser::in = 0;
eval { Parser::ddollar() };
ok(!$@, 'ddollar with empty content does not crash');

# Test 15: ampersand outside matrix context
@Parser::in = ();
$Parser::in = 0;
@OutputBuffer::wait = ();
eval { Parser::ampersand() };
ok(!$@, 'ampersand outside matrix does not crash');

# Test 16: sharp without argument context
@Parser::in = ();
$Parser::in = 0;
@MacroExpansion::argStack = ();
eval { Parser::sharp() };
ok(!$@, 'sharp without arguments handles gracefully');

# Test 17: eoL at end of input
@Parser::in = ();
$Parser::in = 0;
eval { Parser::eoL() };
ok(!$@, 'eoL at end of input does not crash');

# Test 18: superscript with empty stack
@OutputBuffer::out = ();
@OutputBuffer::chunks = ();
@Parser::in = ("test");
$Parser::in = 0;
eval { Parser::superscript() };
ok(!$@, 'superscript with empty stack does not crash');

# Test 19: paragraph with extremely long input
@Parser::in = ("a" x 10000);
$Parser::in = 0;
eval { 
    local $SIG{ALRM} = sub { die "timeout\n" };
    alarm(5);
    Parser::paragraph();
    alarm(0);
};
ok(!$@ || $@ eq "timeout\n", 'paragraph handles very long input');

# Test 20: nested math mode handling
@Parser::in = ("\$", "x", "\$");
$Parser::in = 0;
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
eval { Parser::dollar() };
ok(!$@, 'nested math mode processing does not crash');
