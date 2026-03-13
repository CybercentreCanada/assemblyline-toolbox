
from assemblyline_toolbox import get_hostip


def test_entropy():
    assert isinstance(get_hostip(), str)
    assert len(get_hostip()) > 0
