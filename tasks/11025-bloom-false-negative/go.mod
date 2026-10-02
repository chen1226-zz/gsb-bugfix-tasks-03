module github.com/bits-and-blooms/bloom/v3

go 1.26

require (
	github.com/bits-and-blooms/bitset v1.24.4
	github.com/twmb/murmur3 v1.1.8
)

replace github.com/bits-and-blooms/bitset => ./deps/bitset

replace github.com/twmb/murmur3 => ./deps/murmur3
