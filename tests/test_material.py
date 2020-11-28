import pytest


def test_factory():
    from solcore.material import Material
    from pint import Quantity as Q_
    import xarray as xr

    # Get some parameters from the database and and an external parameter
    mat = Material.factory(name="GaAs", include=("band_gap",), T=Q_(300, "K"))
    assert "band_gap" in mat.params
    assert "T" in mat.params

    # nk data is not valid
    nk = xr.DataArray([1, 2, 3])
    with pytest.raises(ValueError):
        Material.factory(name="GaAs", nk=nk)

    # nk data is valid
    nk = xr.DataArray([1, 2, 3], dims=["wavelength"], coords={"wavelength": [0, 1, 2]})
    mat = Material.factory(name="GaAs", nk=nk)
    xr.testing.assert_equal(nk, mat._nk)


def test_from_dict():
    from solcore.material import Material
    import xarray as xr

    nk = xr.DataArray([1, 2, 3], dims=["wavelength"], coords={"wavelength": [0, 1, 2]})
    data = dict(name="my mat", T=300, comp={"Fe": 0.1}, nk=nk, weight=42)

    mat = Material.from_dict(**data)
    assert mat.name == "my mat"
    assert mat.comp["Fe"] == 0.1
    xr.testing.assert_equal(nk, mat.nk)
    assert "weight" in mat.params

    nk = xr.DataArray([1, 2, 3])
    data = dict(name="my mat", T=300, comp={"Fe": 0.1}, nk=nk, weight=42)
    with pytest.raises(ValueError):
        Material.from_dict(**data)


def test_get_attribute():
    from solcore.material import Material
    from pint import Quantity as Q_

    mat = Material.factory(name="GaAs", T=Q_(300, "K"))
    assert mat.band_gap
    assert mat.T == Q_(300, "K")


def test_material_str():
    from solcore.material import Material

    mat = Material.factory(name="FeO", comp={"Fe": 0.1})
    assert mat.material_str == "Fe0.1O"


def test_to_dict():
    from solcore.material import Material
    import xarray as xr

    nk = xr.DataArray([1, 2, 3], dims=["wavelength"], coords={"wavelength": [0, 1, 2]})
    data = dict(name="my mat", T=300, comp={"Fe": 0.1}, nk=nk, weight=42)
    mat = Material.from_dict(**data)

    new_dict = mat.to_dict()
    for k in data.keys():
        if k == "nk":
            continue
        assert data[k] == new_dict[k]

    xr.testing.assert_equal(data["nk"], new_dict["nk"])
