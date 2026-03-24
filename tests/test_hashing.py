import pytest
from assemblyline_toolbox import SsdeepHasher, TlshHasher

SAMPLE = b"A very interesting block of sample text that is totally innocent and can't be faulted in any way."
SAMPLE_TLSH = 'T1DBB012133606459DC6D122400D002BEC233182FC6ED074E048E473F923050C11579351'


def test_ssdeep():
    calculator = SsdeepHasher()
    assert calculator.digest() is not None

    calculator = SsdeepHasher()
    calculator.update(SAMPLE[0:10])
    calculator.update(SAMPLE[10:])
    assert calculator.digest() == '3:M0HLGiKZOER2WFsPsI4FT205JiMLi:M0iSERW3ITiKi'

    calculator = SsdeepHasher(len(SAMPLE))
    calculator.update(SAMPLE)
    assert calculator.digest() == '3:M0HLGiKZOER2WFsPsI4FT205JiMLi:M0iSERW3ITiKi'

    assert SsdeepHasher.hash(SAMPLE) == '3:M0HLGiKZOER2WFsPsI4FT205JiMLi:M0iSERW3ITiKi'
    assert SsdeepHasher.hash(SAMPLE.decode()) == '3:M0HLGiKZOER2WFsPsI4FT205JiMLi:M0iSERW3ITiKi'

    with pytest.raises(ValueError, match='fixed size'):
        calculator = SsdeepHasher(len(SAMPLE))
        calculator.update(SAMPLE * 2)
        calculator.digest()


def test_tlsh():
    calculator = TlshHasher()
    assert calculator.digest() is None

    calculator = TlshHasher()
    calculator.update(SAMPLE[0:10])
    calculator.update(SAMPLE[10:])
    assert calculator.digest() == SAMPLE_TLSH

    assert TlshHasher.hash(SAMPLE) == SAMPLE_TLSH
    assert TlshHasher.hash(SAMPLE.decode()) == SAMPLE_TLSH
