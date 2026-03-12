import pytest
from assemblyline_toolbox import SsdeepHasher

SAMPLE = b"A very interesting block of sample text that is totally innocent and can't be faulted in any way."


def test_ssdeep():

    calculator = SsdeepHasher()
    print(calculator.digest())

    calculator = SsdeepHasher()
    calculator.update(SAMPLE[0:10])
    calculator.update(SAMPLE[10:])
    assert calculator.digest() == '3:M0HLGiKZOER2WFsPsI4FT205JiMLi:M0iSERW3ITiKi'

    calculator = SsdeepHasher(len(SAMPLE))
    calculator.update(SAMPLE)
    assert calculator.digest() == '3:M0HLGiKZOER2WFsPsI4FT205JiMLi:M0iSERW3ITiKi'

    with pytest.raises(ValueError, match='fixed size'):
        calculator = SsdeepHasher(len(SAMPLE))
        calculator.update(SAMPLE * 2)
        calculator.digest()
