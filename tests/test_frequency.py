
import random

from assemblyline_toolbox import BufferedCalculator


def test_entropy():

    calculator = BufferedCalculator()
    assert calculator.entropy() == 0

    calculator = BufferedCalculator()
    calculator.update(b"1" * 10000)
    assert calculator.entropy() == 0
    assert calculator.len() == 10000

    calculator = BufferedCalculator()
    calculator.update(bytes([random.randint(1, 255) for _ in range(10000)]))
    assert calculator.entropy() > 7.5
    assert calculator.len() == 10000


