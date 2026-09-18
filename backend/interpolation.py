"""
Spatial interpolation of groundwater depth readings across a region.

Uses Inverse Distance Weighting (IDW) by default, which needs no extra
dependencies and works fine with a handful to a few hundred stations.
For larger networks or where spatial correlation structure matters more,
swap `idw_interpolate` for ordinary/universal kriging via the `pykrige`
package -- the function signature below is written so that's a drop-in
replacement (points, values, grid_x, grid_y -> grid_z).
"""

import numpy as np


def build_grid(points: np.ndarray, resolution: float = 0.05, padding: float = 0.2):
    """
    points: (N, 2) array of [longitude, latitude]
    Returns grid_x, grid_y meshgrids covering the station bounding box + padding.
    """
    points = np.asarray(points)
    lon_min, lon_max = points[:, 0].min() - padding, points[:, 0].max() + padding
    lat_min, lat_max = points[:, 1].min() - padding, points[:, 1].max() + padding

    grid_lon = np.arange(lon_min, lon_max, resolution)
    grid_lat = np.arange(lat_min, lat_max, resolution)
    grid_x, grid_y = np.meshgrid(grid_lon, grid_lat)
    return grid_x, grid_y


def idw_interpolate(points, values, grid_x, grid_y, power: float = 2.0, eps: float = 1e-9):
    """
    points: (N, 2) array of [longitude, latitude] for each station
    values: (N,) array of the measured depth at each station
    grid_x, grid_y: meshgrid arrays defining the target grid
    power: distance decay exponent (higher = more local influence)
    Returns grid_z, same shape as grid_x, with interpolated depth values.
    """
    points = np.asarray(points)
    values = np.asarray(values)
    shape = grid_x.shape
    gx = grid_x.ravel()
    gy = grid_y.ravel()

    result = np.empty(len(gx))
    for i in range(len(gx)):
        dx = points[:, 0] - gx[i]
        dy = points[:, 1] - gy[i]
        dist = np.sqrt(dx ** 2 + dy ** 2) + eps
        weights = 1.0 / (dist ** power)
        result[i] = np.sum(weights * values) / np.sum(weights)

    return result.reshape(shape)
