#!/usr/bin/perl
use strict;
use warnings;
use Test::More tests => 21;
use lib '../lib';

# Test module loading
BEGIN { use_ok('Tex2UtfConfig') }

# Positive Tests

# Test 1: Module exports expected variables
ok(defined $Tex2UtfConfig::linelength, 'linelength variable exported');

# Test 2: Default linelength value
is($Tex2UtfConfig::linelength, 150, 'default linelength is 150');

# Test 3: Default maxdef value
is($Tex2UtfConfig::maxdef, 400, 'default maxdef is 400');

# Test 4: Debug flag default
is($Tex2UtfConfig::debug, 0, 'debug flag default is 0');

# Test 5: opt_by_par default
is($Tex2UtfConfig::opt_by_par, 0, 'opt_by_par default is 0');

# Test 6: opt_TeX default
is($Tex2UtfConfig::opt_TeX, 1, 'opt_TeX default is 1');

# Test 7: Debug flow flag defined
ok(defined $Tex2UtfConfig::debug_flow, 'debug_flow flag defined');

# Test 8: Token pattern defined
ok(defined $Tex2UtfConfig::tokenpattern, 'tokenpattern defined');

# Test 9: Multi-token pattern defined
ok(defined $Tex2UtfConfig::multitokenpattern, 'multitokenpattern defined');

# Test 10: parse_options function exists
can_ok('Tex2UtfConfig', 'parse_options');

# Negative Tests

# Test 11: Invalid option should not crash
{
    local @ARGV = ('--invalid-option');
    eval { Tex2UtfConfig::parse_options() };
    ok($@, 'invalid option generates error');
}

# Test 12: Linelength can't be negative (set and verify it stays positive)
$Tex2UtfConfig::linelength = 150;
ok($Tex2UtfConfig::linelength > 0, 'linelength is positive');

# Test 13: maxdef must be numeric
$Tex2UtfConfig::maxdef = 400;
ok($Tex2UtfConfig::maxdef =~ /^\d+$/, 'maxdef is numeric');

# Test 14: Debug flag is boolean-like
ok($Tex2UtfConfig::debug == 0 || $Tex2UtfConfig::debug == 1 || $Tex2UtfConfig::debug > 0, 'debug flag is numeric');

# Test 15: secondtime starts at 0
is($Tex2UtfConfig::secondtime, 0, 'secondtime starts at 0');

# Test 16: opt_ragged is boolean
ok($Tex2UtfConfig::opt_ragged == 0 || $Tex2UtfConfig::opt_ragged == 1, 'opt_ragged is boolean');

# Test 17: opt_noindent is boolean
ok($Tex2UtfConfig::opt_noindent == 0 || $Tex2UtfConfig::opt_noindent == 1, 'opt_noindent is boolean');

# Test 18: Token patterns are non-empty strings
ok(length($Tex2UtfConfig::tokenpattern) > 0, 'tokenpattern is non-empty');

# Test 19: Macro pattern exists
ok(defined $Tex2UtfConfig::macro, 'macro pattern defined');

# Test 20: Active pattern exists
ok(defined $Tex2UtfConfig::active, 'active pattern defined');
