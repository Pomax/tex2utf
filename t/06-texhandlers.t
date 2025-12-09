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
    use_ok('TeXHandlers');
}

# Positive Tests

# Test 1: f_fraction function exists
can_ok('TeXHandlers', 'f_fraction');

# Test 2: f_radical function exists
can_ok('TeXHandlers', 'f_radical');

# Test 3: f_superSub function exists
can_ok('TeXHandlers', 'f_superSub');

# Test 4: f_subSuper function exists
can_ok('TeXHandlers', 'f_subSuper');

# Test 5: f_overline function exists
can_ok('TeXHandlers', 'f_overline');

# Test 6: f_underline function exists
can_ok('TeXHandlers', 'f_underline');

# Test 7: f_not function exists
can_ok('TeXHandlers', 'f_not');

# Test 8: f_putover function exists
can_ok('TeXHandlers', 'f_putover');

# Test 9: f_choose function exists
can_ok('TeXHandlers', 'f_choose');

# Test 10: f_buildrel function exists
can_ok('TeXHandlers', 'f_buildrel');

# Negative Tests

# Test 11: f_fraction with insufficient records
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
eval { TeXHandlers::f_fraction() };
ok($@, 'f_fraction with empty buffer fails');

# Test 12: f_radical with empty buffer
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
eval { TeXHandlers::f_radical() };
ok($@, 'f_radical with empty buffer fails');

# Test 13: f_overline with empty buffer
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
eval { TeXHandlers::f_overline() };
ok($@, 'f_overline with empty buffer fails');

# Test 14: f_underline with empty buffer
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
eval { TeXHandlers::f_underline() };
ok($@, 'f_underline with empty buffer fails');

# Test 15: f_leftright function exists
can_ok('TeXHandlers', 'f_leftright');

# Test 16: f_arrow function exists
can_ok('TeXHandlers', 'f_arrow');

# Test 17: f_arrow_v function exists
can_ok('TeXHandlers', 'f_arrow_v');

# Test 18: f_widehat function exists
can_ok('TeXHandlers', 'f_widehat');

# Test 19: f_widetilde function exists
can_ok('TeXHandlers', 'f_widetilde');

# Test 20: f_discard function exists
can_ok('TeXHandlers', 'f_discard');
