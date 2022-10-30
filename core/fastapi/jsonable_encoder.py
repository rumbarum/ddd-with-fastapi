from functools import partial

import numpy as np
from fastapi.encoders import jsonable_encoder
from pandas import Timestamp

custom_encoder = {
    np.integer: float,
    np.floating: float,
    np.ndarray: lambda x: x.tolist(),
    Timestamp: lambda x: x.timestamp(),
}

custom_jsonable_encoder = partial(jsonable_encoder, custom_encoder=custom_encoder)
