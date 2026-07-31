from x2py.contracts import Addr, Int32, String, bind

@bind("fixed_array_extent")
def fixed_array_extent_raw(labels: Addr(String[8][2])) -> Int32: ...
