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
}

# Positive Tests

# Test 1: start function exists
can_ok('LevelManager', 'start');

# Test 2: finish function exists
can_ok('LevelManager', 'finish');

# Test 3: finish_ignore function exists
can_ok('LevelManager', 'finish_ignore');

# Test 4: collapse function exists
can_ok('LevelManager', 'collapse');

# Test 5: collapseAll function exists
can_ok('LevelManager', 'collapseAll');

# Test 6: assertHave function exists
can_ok('LevelManager', 'assertHave');

# Test 7: trim function exists
can_ok('LevelManager', 'trim');

# Test 8: start increases level depth
@OutputBuffer::level = (0);
@OutputBuffer::chunks = (0);
@OutputBuffer::out = ();
@OutputBuffer::tokenByToken = (0);
@OutputBuffer::wait = ();
@OutputBuffer::action = ();
my $initial_level = scalar(@OutputBuffer::level);
LevelManager::start("}");
ok(scalar(@OutputBuffer::level) > $initial_level, 'start increases level depth');

# Test 9: assertHave returns true for valid chunks
@OutputBuffer::level = (0);
@OutputBuffer::chunks = (0);
@OutputBuffer::out = (Records::string2record("test"));
my $has_chunks = LevelManager::assertHave(1);
ok($has_chunks, 'assertHave returns true for existing chunks');

# Test 10: trim_beg function exists
can_ok('LevelManager', 'trim_beg');

# Negative Tests

# Test 11: assertHave returns false for missing chunks
@OutputBuffer::level = (0, 1);
@OutputBuffer::chunks = (0);
my $missing = LevelManager::assertHave(10);
ok(!$missing, 'assertHave returns false for missing chunks');

# Test 12: finish on empty level structure
@OutputBuffer::level = (0);
@OutputBuffer::chunks = (0);
@OutputBuffer::out = ();
@OutputBuffer::wait = ();
@OutputBuffer::action = ();
@OutputBuffer::tokenByToken = (0);
eval { LevelManager::finish("test") };
ok(!$@, 'finish on minimal structure does not crash');

# Test 13: finish_ignore on empty structure
eval { LevelManager::finish_ignore("test") };
ok(!$@, 'finish_ignore on minimal structure does not crash');

# Test 14: collapse with 0 chunks
@OutputBuffer::level = (0);
@OutputBuffer::chunks = (0);
eval { LevelManager::collapse(0) };
ok(!$@, 'collapse with 0 chunks does not crash');

# Test 15: collapseAll on empty buffer
@OutputBuffer::out = ();
@OutputBuffer::chunks = (0);
@OutputBuffer::level = (0);
eval { LevelManager::collapseAll() };
ok(!$@, 'collapseAll on empty buffer does not crash');

# Test 16: trim with no chunks
@OutputBuffer::chunks = (0);
@OutputBuffer::out = ();
eval { LevelManager::trim(1) };
ok(!$@, 'trim with no chunks does not crash');

# Test 17: trim_end function exists
can_ok('LevelManager', 'trim_end');

# Test 18: trim_one function exists
can_ok('LevelManager', 'trim_one');

# Test 19: collapseOne function exists
can_ok('LevelManager', 'collapseOne');

# Test 20: start with numeric event
@OutputBuffer::level = (0);
@OutputBuffer::chunks = (0);
@OutputBuffer::wait = ();
@OutputBuffer::action = ();
@OutputBuffer::tokenByToken = (0);
eval { LevelManager::start(2) };
ok(!$@, 'start with numeric event does not crash');
