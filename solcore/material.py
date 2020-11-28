from __future__ import annotations

from typing import Optional, Hashable, Tuple, Dict, Any

import xarray as xr
import pandas as pd
from pint import Quantity as Q_
from frozendict import frozendict

from solcore.parameter import ParameterManager, Parameter


class Material:
    def __init__(
        self,
        name: str,
        comp: Optional[dict] = None,
        sources: Tuple[str, ...] = (),
        nk: xr.DataArray = xr.DataArray(),
        params: Optional[dict] = None,
    ):
        # Define the types
        self.name: str
        self.comp: frozendict
        self.sources: Tuple[str, ...]
        self._nk: xr.DataArray
        self._params: Dict[str, Q_]

        # Actually create the attributes. Needed this way since it is inmutable
        composition = frozendict(comp if isinstance(comp, dict) else {})
        parameters = params if isinstance(params, dict) else {}
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "comp", composition)
        object.__setattr__(self, "sources", tuple(sources))
        object.__setattr__(self, "_nk", nk)
        object.__setattr__(self, "_params", parameters)

    def __getattr__(self, item: str) -> Q_:
        """Retrieve attributes for the material.

        If the requested attribute is not already in the params dictionary, then it will
        be retrieved from the available sources and the result stored in the sources.

        Raises:
            ParameterMissing: If the requested attribute does not exists in the
                parameters dictionary not in any of the available databases.

        Return:
            The value of the parameter.
        """
        if item not in self._params:
            self._params[item] = ParameterManager().get_parameter(
                material=self.name,
                parameter=item,
                source=self.sources,
                comp=self.comp,
                **self._params,
            )
        return self._params[item]

    def __setattr__(self, item, value) -> Any:
        raise NotImplementedError("Attributes of a Material object cannot be change.")

    def __delattr__(self, item):
        raise NotImplementedError("Attributes of a Material object cannot be deleted.")

    @property
    def params(self) -> Tuple[str, ...]:
        """List of parameters already stored in the material."""
        return tuple(self._params.keys())

    def nk(self) -> xr.DataArray:
        """DataArray with the complex refractive index of the material.

        Raises:
            ParameterMissing: If the requested attribute does not exists in the
                parameters dictionary not in any of the available databases.

        Return:
            The refractive index
        """
        if self._nk.shape == ():
            self._nk = ParameterManager().get_nk(
                material=self.name, source=self.sources, comp=self.comp, **self._params,
            )
        return self._nk

    @classmethod
    def factory(
        cls,
        name: str,
        comp: Optional[dict] = None,
        include: Tuple[str, ...] = (),
        sources: Tuple[str, ...] = (),
        **kwargs,
    ) -> Material:
        """Create a material object out of the existing databases.

        Args:
            name: Name of the material.
            comp: Composition of the material, eg. {"In": 0.17}. If more
                than one element is given, then the first one will become x, the
                 second y, etc.
            include: Parameters to retrieve form the sources during the creation of
                the material. Any parameter can be retrieved later on, as well.
            sources: Sources in which to look for parameters. By default, all of the
                available sources are used. If provided, the sources will be scanned
                in the the order given.
            **kwargs: Any extra argument will be incorporated to the parameters
                dictionary. These have preference over the parameters built into
                Solcore. They should be Quantities, otherwise the results and errors
                might be unexpected. Common arguments are the temperature (T) and the
                doping density (Na and Nd).

        Returns:
            A new Material object.
        """
        comp = comp if comp else {}

        to_retrieve = tuple((p for p in include if p != "nk"))
        params: Dict[str, Parameter] = (
            ParameterManager().get_multiple_parameters(
                material=name, include=to_retrieve, source=sources, comp=comp, **kwargs
            )
            if to_retrieve != ()
            else {}
        )
        params.update(kwargs)

        nk = params.get("nk", xr.DataArray())
        if nk.shape != ():
            cls._validate_nk(nk)
        elif "nk" in include:
            nk = ParameterManager().get_nk(
                material=name, source=sources, comp=comp, **kwargs
            )

        return cls(name=name, comp=comp, sources=sources, nk=nk, params=params)

    @classmethod
    def from_dict(cls, **kwargs) -> Material:
        """Construct a material object from a plain, unpacked dictionary.

        Any entry that is not "name", "comp", "sources" or "nk" is bundled together as
        "params".

        Args:
            data (dict): A dictionary with all the material information. Composition
                should be a dictionary itself.

        Returns:
            A new Material object.
        """
        try:
            name = kwargs.pop("name")
        except KeyError:
            raise KeyError(
                "'name' is a required field in the input dictionary when  creating a "
                "material."
            )

        comp = kwargs.pop("comp", {})
        sources = kwargs.pop("sources", ())
        nk = kwargs.pop("nk", xr.DataArray())

        if nk.shape != ():
            cls._validate_nk(nk)

        return cls(name, comp, sources, nk, kwargs)

    @classmethod
    def from_dataframe(
        cls, data: pd.DataFrame, index: Hashable = 0, nk: xr.DataArray = xr.DataArray()
    ) -> Material:
        """Construct a material object from a pandas DataFrame.

        Args:
            data: A DataFrame with all the material information. Composition entry
                should be a dictionary of key: value pairs.
            index: Index label from where to retrieve the data. By default,
                index = 0 is used.
            nk: Optionally, an xarray with the refractive index information for this
                material.

        Returns:
            A new Material object.
        """
        try:
            name = data.loc[index, "name"]
        except KeyError:
            raise KeyError(
                "'name' is a required field in the input DataFrame when creating a "
                "Material."
            )

        comp = data.loc[index, "comp"] if "comp" in data else {}
        sources = data.loc[index, "sources"] if "sources" in data else ()
        param_cols = [k for k in data.columns if k not in ("name", "comp", "sources")]
        kwargs = data.loc[index, param_cols].to_dict()

        if nk.shape != ():
            cls._validate_nk(nk)

        return cls(name, comp, sources, nk, **kwargs)

    @property
    def material_str(self) -> str:
        """Return the material name embedding the composition information."""
        result = self.name
        for k, v in self.comp.items():
            result = result.replace(k, f"{k}{v:.2}")
        return result

    def to_dict(self) -> dict:
        """Provide all the Material information as a plain dictionary.

        Returns:
            A dictionary with all the material information.
        """
        result = dict(name=self.name, comp=self.comp, sources=self.sources, nk=self._nk)
        result.update(self._params)
        return result

    def to_dataframe(self) -> pd.DataFrame:
        """Provide all the Material information as a pandas DataFrame.

        Note that this does not include the refractive index data, 'nk', if present.

        Returns:
            A DataFrame with the material information.
        """
        asdict = self.to_dict()
        asdict["comp"] = [asdict["comp"]]
        asdict.pop("nk")
        return pd.DataFrame.from_dict(asdict)

    @staticmethod
    def _validate_nk(nk: xr.DataArray) -> None:
        """Validates if an nk entry is actually an xarray with the correct features"""
        if not isinstance(nk, xr.DataArray):
            raise TypeError("The value for 'nk' must be of type 'xr.DataArray'.")
        if "wavelength" not in nk.dims or "wavelength" not in nk.coords:
            msg = "'wavelength' is not a DataArray dimension and coordinate."
            raise ValueError(msg)

    def __repr__(self) -> str:
        nk = self._nk.__repr__().replace("\n", " ")
        return (
            f"<Material(name={self.name}, comp={self.comp._dict}, "
            f"sources={self.sources}, nk={nk}, params={self._params})>"
        )


if __name__ == "__main__":
    from pprint import pp

    gaas = Material.factory("GaAs", include=("band_gap", "nk",), T=Q_(300, "K"),)
    pp(gaas)
