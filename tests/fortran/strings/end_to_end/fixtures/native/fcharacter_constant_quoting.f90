module quoting_mod
  use iso_c_binding, only : c_char
  implicit none
  character(len=5), parameter :: word = 'don''t'
  character(len=3), parameter :: pair = "a""b"
  character(len=4), parameter :: plain = 'abcd'
  character(kind=c_char, len=3), parameter :: tagged = c_char_'abc'
  character(len=3), parameter :: numbered = 1_'xyz'
  character(len=5), parameter :: tagged_quote = c_char_'don''t'
end module quoting_mod
