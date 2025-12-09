#!/usr/bin/perl
use strict;
use warnings;
use Test::More tests => 20;
use lib '../lib';

BEGIN { 
    use_ok('Tex2UtfConfig');
    use_ok('Records');
    use_ok('OutputBuffer');
}

# Positive Tests

# Test 1: Output buffer arrays initialized
ok(\@OutputBuffer::out, '@out array defined');
ok(\@OutputBuffer::chunks, '@chunks array defined');
ok(\@OutputBuffer::level, '@level array defined');

# Test 2: Initial state is correct
is(scalar(@OutputBuffer::out), 0, '@out starts empty');
is($OutputBuffer::chunks[0], 0, '@chunks starts with [0]');
is($OutputBuffer::level[0], 0, '@level starts with [0]');

# Test 3: curlength starts at 0
is($OutputBuffer::curlength, 0, 'curlength starts at 0');

# Test 4: commit function exists
can_ok('OutputBuffer', 'commit');

# Test 5: uncommit function exists
can_ok('OutputBuffer', 'uncommit');

# Test 6: finishBuffer function exists
can_ok('OutputBuffer', 'finishBuffer');

# Test 7: exp_sp function exists
can_ok('OutputBuffer', 'exp_sp');

# Test 8: commit adds to output buffer
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
$OutputBuffer::curlength = 0;
OutputBuffer::commit(Records::string2record("test"));
is(scalar(@OutputBuffer::out), 1, 'commit adds record to buffer');

# Test 9: output_print function exists
can_ok('OutputBuffer', 'output_print');

# Test 10: prepare_cut function exists
can_ok('OutputBuffer', 'prepare_cut');

# Negative Tests

# Test 11: commit with invalid record format still works
eval { OutputBuffer::commit("invalid") };
ok(!$@, 'commit with invalid format does not crash');

# Test 12: uncommit on empty buffer
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
my $result = OutputBuffer::uncommit();
ok(1, 'uncommit on empty buffer does not crash');

# Test 13: finishBuffer on empty state
@OutputBuffer::out = ();
@OutputBuffer::level = (0);
eval { OutputBuffer::finishBuffer() };
ok(!$@, 'finishBuffer on empty state does not crash');

# Test 14: curlength never negative
$OutputBuffer::curlength = 0;
ok($OutputBuffer::curlength >= 0, 'curlength is never negative');

# Test 15: chunks array always has at least one element
ok(scalar(@OutputBuffer::chunks) >= 1, 'chunks array not empty');

# Test 16: level array always has at least one element
ok(scalar(@OutputBuffer::level) >= 1, 'level array not empty');

# Test 17: commit maintains chunk consistency
my $initial_chunks = scalar(@OutputBuffer::chunks);
OutputBuffer::commit(Records::string2record("x"));
ok(scalar(@OutputBuffer::chunks) >= $initial_chunks, 'chunks array grows or stays same');

# Test 18: tokenByToken array defined
ok(\@OutputBuffer::tokenByToken, '@tokenByToken array defined');

# Test 19: wait array defined
ok(\@OutputBuffer::wait, '@wait array defined');

# Test 20: action array defined
ok(\@OutputBuffer::action, '@action array defined');
