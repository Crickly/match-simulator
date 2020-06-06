import pandas as pd


def create_pipeline(*functions):
    def pipeline(_in):
        res = _in
        for function in functions:
            res = function(res)
        return res

    return pipeline


def create_set_index(index):
    def set_index(df):
        return df.set_index(index)

    return set_index


def create_add_missing_row(row, initial_val):
    def add_missing_row(df):
        # check if it exists
        if row not in df.index:
            df.loc[row] = initial_val

        return df

    return add_missing_row


def transpose_df(df):
    return df.T


def create_rename_label(old, new, axis=0):
    def rename_label(df):
        return df.rename({old: new}, axis=axis)

    return rename_label


def create_rename_axis(new):
    def rename_axis(df):
        return df.rename_axis(new)

    return rename_axis


def join_dists(dfs):
    return pd.concat(dfs, axis=1, join="inner")


def create_average_df(axis):
    def average_df(df):
        return df.mean(axis=axis)

    return average_df


def create_fetch_data(query, conn):
    def fetch_data(obj_id):
        return pd.read_sql_query(query.format(obj_id=obj_id), conn)

    return fetch_data


def create_normalise_values(col):
    def normalise_values(df):
        df[col] = df[col] / df[col].sum()

        return df

    return normalise_values


def print_passthrough(val):
    print(val)
    return val
