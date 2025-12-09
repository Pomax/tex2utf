#!/usr/bin/perl
use strict;
use warnings;
use Test::More tests => 23;
use lib '../lib';

BEGIN { 
    use_ok('Tex2UtfConfig');
    use_ok('MacroExpansion');
    use_ok('TeXDefinitions');
}

# Positive Tests

# Test 1: initialize_definitions function exists
can_ok('TeXDefinitions', 'initialize_definitions');

# Test 2: initialize_definitions runs without error
eval { TeXDefinitions::initialize_definitions() };
ok(!$@, 'initialize_definitions runs successfully');

# Test 3: Basic TeX commands defined
TeXDefinitions::initialize_definitions();
ok(exists $TeXDefinitions::type{'\\alpha'}, 'alpha command is defined');

# Test 4: Greek letters defined
ok(exists $TeXDefinitions::type{'\\beta'}, 'beta command is defined');

# Test 5: Math operators defined
ok(exists $TeXDefinitions::type{'\\sum'}, 'sum command is defined');

# Test 6: Content mappings created
ok(defined $TeXDefinitions::contents{'\\alpha'}, 'alpha has content mapping');

# Test 7: Type mappings created
ok(defined $TeXDefinitions::type{'\\alpha'}, 'alpha has type mapping');

# Test 8: Environment definitions
ok(exists $TeXDefinitions::environment{'matrix'}, 'matrix environment defined');

# Test 9: Multiple initializations don't break
TeXDefinitions::initialize_definitions();
TeXDefinitions::initialize_definitions();
ok(exists $TeXDefinitions::type{'\\alpha'}, 'multiple initializations work');

# Test 10: Wide variety of symbols defined
my @expected = qw(\\alpha \\beta \\gamma \\delta \\epsilon \\zeta \\eta \\theta);
my $all_found = 1;
foreach my $sym (@expected) {
    $all_found = 0 unless exists $TeXDefinitions::type{$sym};
}
ok($all_found, 'Greek alphabet symbols are defined');

# Negative Tests

# Test 11: Undefined commands don't exist
ok(!exists $MacroExpansion::type{'notarealcommand'}, 'undefined command does not exist');

# Test 12: Random strings not defined
ok(!exists $MacroExpansion::type{'xyznotdefined'}, 'random string not defined');

# Test 13: Case sensitive checking
TeXDefinitions::initialize_definitions();
ok(!exists $MacroExpansion::type{'ALPHA'}, 'commands are case-sensitive');

# Test 14: Empty command not defined
ok(!exists $MacroExpansion::type{''}, 'empty command not defined');

# Test 15: Whitespace commands not defined
ok(!exists $MacroExpansion::type{' '}, 'whitespace command not defined');

# Test 16: Special characters not blindly defined
ok(!exists $MacroExpansion::type{'@#$%'}, 'invalid characters not defined');

# Test 17: Very long commands not defined
ok(!exists $MacroExpansion::type{'x' x 1000}, 'extremely long commands not defined');

# Test 18: Numeric-only commands not defined
ok(!exists $MacroExpansion::type{'12345'}, 'numeric-only commands not defined');

# Test 19: Commands with spaces not defined
ok(!exists $MacroExpansion::type{'alpha beta'}, 'commands with spaces not defined');

# Test 20: Initialization preserves type hash reference nature
TeXDefinitions::initialize_definitions();
ok(ref(\%TeXDefinitions::type) eq 'HASH', 'type hash remains a hash reference');
