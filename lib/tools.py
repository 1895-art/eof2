"""
Supplementary tools for the meta-data enabled EOF analysis interface.

"""
# (c) Copyright 2010-2012 Andrew Dawson. All Rights Reserved.
#     
# This file is part of eof2.
# 
# eof2 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# eof2 is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU General Public License
# along with eof2.  If not, see <http://www.gnu.org/licenses/>.
import cdms2
import numpy as np

from errors import EofToolError
from nptools import covariance_map as _npcovmap
from nptools import correlation_map as _npcormap


def _rootcoslat_weights(latdim):
    """Square-root of cosine of latitude weights.

    *latdim*
       Latitude dimension values.

    """
    coslat = np.cos(np.deg2rad(latdim))
    coslat[np.where(coslat < 0)] = 0.
    latw = np.sqrt(coslat)
    latw[np.where(np.isnan(latw))] = 0.
    return latw


def _area_weights(grid, gridorder):
    """Area weights.

    *grid*
        :py:mod:`cdms2` grid.

    *gridorder*
        Either "xy" or "yx".

    """
    latw, lonw = grid.getWeights()
    if gridorder == "xy":
        wtarray = np.outer(lonw, latw)
    else:
        wtarray = np.outer(latw, lonw)
    wtarray /= wtarray.sum()
    wtarray = np.sqrt(wtarray)
    return wtarray


def weights_array(dataset, scheme="area"):
    """Weights for a data set on a grid.
    
    Returned weights are a :py:attr:`numpy.ndarray` broadcastable
    against the input data shape.
    
    **Arguments:**

    *dataset*
        A :py:mod:`cdms2` variable to generate weights for.

    **Optional arguments:**

    *scheme*
        Weighting scheme to use. The following values are accepted:

        * *"coslat"* : Square-root of cosine of latitude. The value
          *"cos_lat"* is accepted as an alias.
        * *"area"* : Normalized area weights (default).

    **Examples:**

    Area weights for a :py:mod:`cdms2` variable on 2D grid:

    >>> wts = weights_array(var2d, scheme="area")

    Square-root of cosine of latitude weights for a :py:mod:`cdms2`
    variable with a latitude dimension:

    >>> wts = weights_array(var, scheme="coslat")

    """
    # A re-usable generic error message for the function. When raising an
    # exception just fill in what is required.
    errstr = "weighting scheme '%s' requires %%s" % scheme
    # Always use lower-case for the scheme, allowing the user to use 
    # upper-case in their calling code without an error.
    scheme = scheme.lower()
    if scheme in ("area"):
        # Handle area weighting.
        grid = dataset.getGrid()
        if grid is None:
            raise EofToolError(errstr % "a grid")
        order = dataset.getOrder()
        if "xy" in order:
            gridorder = "xy"
            dimtoindex = dataset.getLatitude()
        elif "yx" in order:
            gridorder = "yx"
            dimtoindex = dataset.getLongitude()
        else:
            raise EofToolError(errstr % \
                    "adjacent latitude and longitude dimensions")
        # Retrieve area weights for the specified grid.
        weights = _area_weights(grid, gridorder)
    elif scheme in ("coslat", "cos_lat"):
        # Handle square-root of cosine of latitude weighting.
        try:
            latdim = dataset.getLatitude()[:]
            dimtoindex = dataset.getLatitude()
        except (AttributeError, TypeError):
            raise EofToolError(errstr % "a latitude dimension")
        # Retrieve latitude weights.
        weights = _rootcoslat_weights(latdim)
    else:
        raise EofToolError("invalid weighting scheme: '%s'" % scheme)
    # Re-shape the retrieved weights so that they are broadcastable to the
    # shape of the input arrays. This just involves adding any additional
    # singleton dimensions to the right of the last weights dimension.
    rightdims = len(dataset.shape) - dataset.getAxisIndex(dimtoindex) - 1
    weights = weights.reshape(weights.shape + (1,)*rightdims)
    return weights

def _covcor_dimensions(pcsaxes, fieldaxes):
    """
    Extract appropriate dimensions for covariance/correlation maps.
    
    """
    try:
        sdims = fieldaxes[1:]
    except IndexError:
        sdims = [None]
    try:
        pdim = pcsaxes[1]
    except IndexError:
        pdim = None
    outdims = filter(None, [pdim] + sdims)
    return outdims


def correlation_map(pcs, field):
    """Correlation maps for a set of PCs and a spatial-temporal field.

    Given a set of PCs in a :py:mod:`cdms2` variable (e.g., as output
    from :py:meth:`eof2.Eof.pcs`) and a spatial-temporal field in a
    :py:mod:`cmds2` variable, one correlation map per PC is computed.

    The field must have the same temporal dimension as the PCs. Any
    number of spatial dimensions (including zero) are allowed in the
    field and there can be any number of PCs.

    **Arguments:**

    *pcs*
        PCs in a :py:mod:`cdms2` variable.

    *field*
        Spatial-temporal field in a :py:mod:`cdms2` variable.

    **Examples:**

    Assuming *eofobj* is an instance of :py:class:`~eof2.Eof`, compute
    correlation maps for each PC:

    >>> pcs = eofobj.pcs(pcscaling=1)
    >>> cormaps = correlation_map(pcs, field)

    """
    cor = _npcormap(pcs.asma(), field.asma())
    outdims = _covcor_dimensions(pcs.getAxisList(), field.getAxisList())
    if not outdims:
        # There are no output dimensions, return a scalar.
        return cor
    # Otherwise return a cdms2 variable with the appropriate dimensions.
    cor = cdms2.createVariable(cor, axes=outdims, id="pccor")
    cor.long_name = "PC correlation"
    cor.units = ""
    return cor


def covariance_map(pcs, field, ddof=1):
    """Covariance maps for a set of PCs and a spatial-temporal field.

    Given a set of PCs in a :py:mod:`cdms2` variable (e.g., as output
    from :py:meth:`eof2.Eof.pcs`) and a spatial-temporal field in a
    :py:mod:`cmds2` variable, one covariance map per PC is computed.

    The field must have the same temporal dimension as the PCs. Any
    number of spatial dimensions (including zero) are allowed in the
    field and there can be any number of PCs.

    **Arguments:**

    *pcs*
        PCs in a :py:mod:`cdms2` variable.

    *field*
        Spatial-temporal field in a :py:mod:`cdms2` variable.

    **Optional arguments:**

    *ddof*
        'Delta degrees of freedom'. The divisor used to normalize
        the covariance matrix is *N - ddof* where *N* is the
        number of samples. Defaults to *1*.
        
    **Examples:**

    Assuming *eofobj* is an instance of :py:class:`~eof2.Eof`, compute
    covariance maps for each PC:

    >>> pcs = eofobj.pcs(pcscaling=1)
    >>> covmaps = covariance_map(pcs, field)

    """
    cov = _npcovmap(pcs.asma(), field.asma(), ddof=ddof)
    outdims = _covcor_dimensions(pcs.getAxisList(), field.getAxisList())
    if not outdims:
        # There are no output dimensions, return a scalar.
        return cov
    # Otherwise return a cdms2 variable with the appropriate dimensions.
    cov = cdms2.createVariable(cov, axes=outdims, id="pccov")
    cov.long_name = "PC covariance"
    return cov


if __name__ == "__main__":
    pass

