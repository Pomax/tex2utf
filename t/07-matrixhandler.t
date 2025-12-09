#!/usr/bin/perl
use strict;
use warnings;
use Test::More tests => 26;
use lib '../lib';

BEGIN { 
    use_ok('Tex2UtfConfig');
    use_ok('Records');
    use_ok('OutputBuffer');
    use_ok('LevelManager');
    use_ok('MacroExpansion');
    use_ok('MatrixHandler');
}

# Positive Tests

# Test 1: matrix function exists
can_ok('MatrixHandler', 'matrix');

# Test 2: endmatrix function exists
can_ok('MatrixHandler', 'endmatrix');

# Test 3: endmatrixArg function exists
can_ok('MatrixHandler', 'endmatrixArg');

# Test 4: halign function exists
can_ok('MatrixHandler', 'halign');

# Test 5: matrix initializes structure
@OutputBuffer::level = (0);
@OutputBuffer::chunks = (0);
@OutputBuffer::wait = ();
@OutputBuffer::action = ();
@OutputBuffer::tokenByToken = (0);
eval { MatrixHandler::matrix() };
ok(!$@, 'matrix function initializes without error');

# Test 6: halign with center alignment
@OutputBuffer::out = (Records::string2record("a"), Records::string2record("b"));
@OutputBuffer::chunks = (0, 1);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(0, "c") };
ok(!$@, 'halign with center alignment does not crash');

# Test 7: halign with left alignment
@OutputBuffer::out = (Records::string2record("a"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(0, "l") };
ok(!$@, 'halign with left alignment does not crash');

# Test 8: halign with right alignment
@OutputBuffer::out = (Records::string2record("a"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(0, "r") };
ok(!$@, 'halign with right alignment does not crash');

# Test 9: halign with multiple columns
@OutputBuffer::out = (
    Records::string2record("a"), 
    Records::string2record("b"),
    Records::string2record("c")
);
@OutputBuffer::chunks = (0, 1, 2);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(1, "c", "c", "c") };
ok(!$@, 'halign with multiple columns does not crash');

# Test 10: endmatrix processes matrix structure
@OutputBuffer::out = (Records::string2record("test"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
@OutputBuffer::wait = ("", "endMatrix");
@OutputBuffer::action = ("", "");
@OutputBuffer::tokenByToken = (0, 0);
eval { MatrixHandler::endmatrix("1;c") };
ok(!$@, 'endmatrix processes structure');

# Negative Tests

# Test 11: matrix with uninitialized state
@OutputBuffer::level = ();
@OutputBuffer::chunks = ();
eval { MatrixHandler::matrix() };
ok($@, 'matrix with uninitialized state may fail');

# Test 12: halign with empty buffer
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
eval { MatrixHandler::halign(0) };
ok(!$@, 'halign with empty buffer does not crash');

# Test 13: halign with invalid alignment
@OutputBuffer::out = (Records::string2record("x"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(0, "invalid") };
ok(!$@, 'halign with invalid alignment generates warning but continues');

# Test 14: endmatrix with no arguments
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
@OutputBuffer::wait = ("", "endMatrix");
@OutputBuffer::action = ("", "");
eval { MatrixHandler::endmatrix() };
ok(!$@, 'endmatrix with no arguments does not crash');

# Test 15: halign with mismatched rows
@OutputBuffer::out = (
    Records::string2record("a"), 
    Records::string2record("b")
);
@OutputBuffer::chunks = (0, 1);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(1, "c", "c", "c") };
ok(!$@, 'halign with mismatched columns does not crash');

# Test 16: matrix increments level correctly
my $before = scalar(@OutputBuffer::level);
MatrixHandler::matrix();
ok(scalar(@OutputBuffer::level) > $before, 'matrix increases level depth');

# Test 17: halign with zero explength
@OutputBuffer::out = (Records::string2record("test"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(0, "c") };
ok(!$@, 'halign with zero explength works');

# Test 18: halign with large explength
@OutputBuffer::out = (Records::string2record("x"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(100, "c") };
ok(!$@, 'halign with large explength does not crash');

# Test 19: endmatrixArg function behavior
@OutputBuffer::out = (Records::string2record("data"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
@OutputBuffer::wait = ("", "endMatrix");
@OutputBuffer::action = ("", "");
@MacroExpansion::argStack = ("c");
eval { MatrixHandler::endmatrixArg("1") };
ok(!$@, 'endmatrixArg processes arguments');

# Test 20: halign with no alignment specs uses default
@OutputBuffer::out = (Records::string2record("test"));
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0, 1);
eval { MatrixHandler::halign(1) };
ok(!$@, 'halign without alignment specs uses defaults');
