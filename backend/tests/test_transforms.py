import pytest

from app.usd import TransformError, fit_bounds


def test_nonuniform_fit_centers_authored_pivot():
    fit = fit_bounds((-1, -2, 0), (1, 2, 4), (2, 4, 8))
    assert fit.scale == pytest.approx((1, 1, 2))
    assert fit.translation == pytest.approx((0, 0, -4))


def test_proportion_preserving_fit_uses_smallest_ratio():
    fit = fit_bounds((0, 0, 0), (2, 4, 8), (4, 4, 4), preserve_proportions=True)
    assert fit.scale == pytest.approx((.5, .5, .5))


@pytest.mark.parametrize("args", [((0, 0, 0), (0, 1, 1), (1, 1, 1)), ((0, 0, 0), (1, 1, 1), (1, 0, 1)), ((0, 0, 0), (1, float('inf'), 1), (1, 1, 1))])
def test_degenerate_and_nonfinite_fits_rejected(args):
    with pytest.raises(TransformError):
        fit_bounds(*args)
