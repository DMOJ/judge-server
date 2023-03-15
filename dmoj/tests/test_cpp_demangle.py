import unittest

from dmoj.utils.cpp_demangle import demangle


class CppDemangleTest(unittest.TestCase):
    def test_valid_demangle(self):
        self.assertEqual(demangle(b'St9bad_alloc'), b'std::bad_alloc')
        self.assertEqual(demangle(b'_Z1hic'), b'h(int, char)')
        self.assertEqual(demangle(b'_ZN9wikipedia7article6formatEv'), b'wikipedia::article::format()')
        self.assertEqual(
            demangle(b'_ZN9wikipedia7article8print_toERSo'), b'wikipedia::article::print_to(std::ostream&)'
        )
        self.assertEqual(
            demangle(b'_ZN9wikipedia7article8wikilinkC1ERKSs'),
            b'wikipedia::article::wikilink::wikilink(std::string const&)',
        )
        self.assertEqual(
            demangle(b'_ZNK3MapI10StringName3RefI8GDScriptE10ComparatorIS0_E16DefaultAllocatorE3hasERKS0_'),
            b'Map<StringName, Ref<GDScript>, Comparator<StringName>, DefaultAllocator>::has(StringName const&) const',
        )

    def test_invalid_demangle(self):
        for invalid in [b'std::bad_alloc', b'\1\2\3\r\n']:
            self.assertEqual(demangle(invalid), invalid)
