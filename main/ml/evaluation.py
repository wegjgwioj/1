# coding:utf-8
from sklearn.metrics import mean_absolute_error, r2_score

try:
    from sklearn.metrics import root_mean_squared_error
except ImportError:  # pragma: no cover
    root_mean_squared_error = None


def regression_metrics(y_true, y_pred):
    if root_mean_squared_error is not None:
        rmse = root_mean_squared_error(y_true, y_pred)
    else:  # pragma: no cover
        from sklearn.metrics import mean_squared_error

        rmse = mean_squared_error(y_true, y_pred, squared=False)
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(rmse),
        "R2": float(r2_score(y_true, y_pred)),
    }
