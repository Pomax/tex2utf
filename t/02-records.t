#!/usr/bin/perl
use strict;
use warnings;
use Test::More tests => 22;
use lib '../lib';

BEGIN { 
    use_ok('Tex2UtfConfig');
    use_ok('Records');
}

# Positive Tests

# Test 1: empty record creation
my $empty = Records::empty();
like($empty, qr/^0,0,0,0,$/, 'empty record format correct');

# Test 2: string to record conversion
my $rec = Records::string2record("hello");
like($rec, qr/^\d+,5,0,\d+,hello$/, 'string2record creates valid record');

# Test 3: get_length function
my $len = Records::get_length("0,5,0,0,hello");
is($len, 5, 'get_length returns correct length');

# Test 4: get_height function
my $height = Records::get_height("2,5,0,0,line1\nline2");
is($height, 2, 'get_height returns correct height');

# Test 5: join two records
my $rec1 = Records::string2record("foo");
my $rec2 = Records::string2record("bar");
my $joined = Records::join_records($rec1, $rec2);
like($joined, qr/foobar/, 'join_records combines strings');

# Test 6: vStack two records
my $v1 = Records::string2record("top");
my $v2 = Records::string2record("bottom");
my $vstacked = Records::vStack($v1, $v2);
like($vstacked, qr/top\nbottom/, 'vStack creates vertical stack');

# Test 7: center a record
my $to_center = Records::string2record("x");
my $centered = Records::center(10, $to_center);
my $centered_len = Records::get_length($centered);
is($centered_len, 10, 'center expands record to specified length');

# Test 8: cut a record
my $long_rec = Records::string2record("hello world");
my @cut_parts = Records::cut(5, $long_rec);
is(scalar(@cut_parts), 2, 'cut returns two parts');

# Test 9: vputs creates vertical string
my $vert = Records::vputs("abc", 1);
like($vert, qr/a\nb\nc/, 'vputs creates vertical string');

# Test 10: setbaseline modifies record
my $test_rec = "2,5,0,0,test";
Records::setbaseline($test_rec, 1);
like($test_rec, qr/^2,5,1/, 'setbaseline updates baseline value');

# Negative Tests

# Test 11: get_length with invalid format
my $invalid_len = Records::get_length("invalid");
is($invalid_len, 0, 'get_length returns 0 for invalid format');

# Test 12: get_height with invalid format
my $invalid_height = Records::get_height("invalid");
is($invalid_height, 0, 'get_height returns 0 for invalid format');

# Test 13: empty record has zero length
my $empty_len = Records::get_length(Records::empty());
is($empty_len, 0, 'empty record has length 0');

# Test 14: cut with negative length returns original
my $cut_test = Records::string2record("test");
my @neg_cut = Records::cut(-5, $cut_test, "fallback");
is($neg_cut[0], "fallback", 'cut with negative length returns fallback');

# Test 15: string2record with empty string
my $empty_str = Records::string2record("");
like($empty_str, qr/^0,0,0,0,$/, 'empty string creates zero-length record');

# Test 16: join with empty records
my $empty1 = Records::empty();
my $empty2 = Records::empty();
my $joined_empty = Records::join_records($empty1, $empty2);
ok(defined $joined_empty, 'joining empty records produces result');

# Test 17: center with length smaller than content
my $too_long = Records::string2record("verylongtext");
my $centered_small = Records::center(5, $too_long);
ok(defined $centered_small, 'center with small length still works');

# Test 18: vStack with empty records
my $vstack_empty = Records::vStack(Records::empty(), Records::empty());
ok(defined $vstack_empty, 'vStack with empty records produces result');

# Test 19: record_forcelength modifies length field
my $force_rec = "1,10,0,0,test";
Records::record_forcelength($force_rec, 5);
like($force_rec, qr/^1,5,/, 'record_forcelength changes length field');

# Test 20: printrecord with valid record (capture output)
{
    my $output = '';
    open my $fh, '>', \$output;
    my $old_fh = select $fh;
    Records::printrecord("0,4,0,0,test");
    select $old_fh;
    like($output, qr/test/, 'printrecord outputs record content');
}
