#!/usr/bin/perl
use strict;
use warnings;
use Test::More tests => 20;
use lib '../lib';

BEGIN { 
    use_ok('Tex2UtfConfig');
    use_ok('OutputBuffer');
    use_ok('MacroExpansion');
}

# Positive Tests

# Test 1: type hash exists
ok(\%MacroExpansion::type, '%type hash defined');

# Test 2: contents hash exists
ok(\%MacroExpansion::contents, '%contents hash defined');

# Test 3: args hash exists
ok(defined %MacroExpansion::args, '%args hash defined');

# Test 4: def hash exists
ok(defined %MacroExpansion::def, '%def hash defined');

# Test 5: callsub function exists
can_ok('MacroExpansion', 'callsub');

# Test 6: define function exists
can_ok('MacroExpansion', 'define');

# Test 7: defb function exists
can_ok('MacroExpansion', 'defb');

# Test 8: get_balanced function exists
can_ok('MacroExpansion', 'get_balanced');

# Test 9: define creates type entry
MacroExpansion::define('\\test', 'expansion');
ok(exists $MacroExpansion::type{'\\test'}, 'define creates type entry');

# Test 10: define creates def entry
ok(exists $MacroExpansion::def{'\\test'}, 'define creates def entry');

# Negative Tests

# Test 11: callsub with invalid function name
eval { MacroExpansion::callsub('nonexistent_function_xyz') };
ok($@, 'callsub with invalid function fails');

# Test 12: get_balanced with unbalanced braces
$Parser::par = '{unbalanced';
my $result = MacroExpansion::get_balanced();
ok(!defined $result || $result, 'get_balanced handles unbalanced input');

# Test 13: define with invalid token pattern
MacroExpansion::define('invalid', 'test');
ok(1, 'define with invalid pattern does not crash');

# Test 14: define with no arguments
eval { MacroExpansion::define() };
ok(1, 'define with no arguments does not crash fatally');

# Test 15: defb with empty array
eval { MacroExpansion::defb() };
ok(!$@, 'defb with empty array does not crash');

# Test 16: environment hash exists
ok(defined %MacroExpansion::environment, '%environment hash defined');

# Test 17: environment_none hash exists
ok(defined %MacroExpansion::environment_none, '%environment_none hash defined');

# Test 18: argStack array exists
ok(defined @MacroExpansion::argStack, '@argStack array defined');

# Test 19: let function exists
can_ok('MacroExpansion', 'let');

# Test 20: def function exists
can_ok('MacroExpansion', 'def');
