import pandas as pd
import pipeline as pipe

#
# Queries
#


bowler_query = """
select
    sum(bowl_wickets_lbw) lbw,
    sum(bowl_wickets_bowled) b,
    sum(bowl_wickets_stumped) st,
    sum(bowl_wickets_caught) ct
from
    core_bowlperformance
where
    core_bowlperformance.player_id = 8058
"""

batsman_query = """
select
    bat_how_out how_out,
    count(1) counts
from
    core_batperformance
where
    core_batperformance.bat_how_out not in ('not out', 'no', 'DNB')
and
    core_batperformance.player_id = {obj_id}
group by bat_how_out;
"""

ground_query = """
select
    bat_how_out how_out,
    count(1) counts
from
    core_batperformance
    inner join core_match on core_batperformance.match_id=core_match.id
where
    core_batperformance.bat_how_out not in ('not out', 'no', 'DNB')
and
    core_match.ground_id = {obj_id}
group by bat_how_out;
"""

global_query = """
select
    bat_how_out how_out,
    count(1) counts
from
    core_batperformance
    inner join core_match on core_batperformance.match_id=core_match.id
    inner join core_competition on core_match.competition_id=core_competition.id
where
    core_batperformance.bat_how_out not in ('not out', 'no', 'DNB')
and
    core_competition.league_id = {obj_id}
group by bat_how_out;
"""


#
# Pipelines
#


clean_data_pipeline = pipe.create_pipeline(
    pipe.create_add_missing_row("lbw", 0),
    pipe.create_add_missing_row("ct", 0),
    pipe.create_add_missing_row("b", 0),
    pipe.create_add_missing_row("run out", 0),
    pipe.create_add_missing_row("st", 0),
    pipe.create_rename_label("run out", "ro", axis=0),
)


def bowler_pipeline(conn):
    return pipe.create_pipeline(
        pipe.create_fetch_data(bowler_query, conn),
        pipe.transpose_df,
        pipe.create_rename_axis("how_out"),
        pipe.create_rename_label(0, "bowler_dist", axis=1),
        clean_data_pipeline,
        pipe.create_normalise_values("bowler_dist"),
    )


def general_dist_pipeline(conn, query, dist_label):
    return pipe.create_pipeline(
        pipe.create_fetch_data(query, conn),
        pipe.create_set_index("how_out"),
        pipe.create_rename_label("counts", dist_label, axis=1),
        clean_data_pipeline,
        pipe.create_normalise_values(dist_label),
    )


def create_get_all_dists(conn):
    def get_all_dists(kwargs):
        return (
            bowler_pipeline(conn)(kwargs["bowler_id"]),
            general_dist_pipeline(conn, batsman_query, "batsman_dist")(
                kwargs["batsman_id"]
            ),
            general_dist_pipeline(conn, ground_query, "ground_dist")(
                kwargs["ground_id"]
            ),
            general_dist_pipeline(conn, global_query, "global_dist")(
                kwargs["league_id"]
            ),
        )

    return get_all_dists


def create_get_dist_pipeline(conn):
    return pipe.create_pipeline(
        create_get_all_dists(conn), pipe.join_dists, pipe.create_average_df(1)
    )


if __name__ == "__main__":

    import sshtunnel
    import mysql.connector

    host = "vision.local"
    localhost = "127.0.0.1"
    ssh_username = "rileyevans"
    ssh_private_key = "~/.ssh/id_rsa"
    user = "crickettesting_django"
    password = "-N3gdCp-K7WN"
    database = "crickly-testing_django"
    server = sshtunnel.SSHTunnelForwarder(
        (host, 22),
        ssh_username=ssh_username,
        ssh_private_key=ssh_private_key,
        remote_bind_address=("localhost", 3306),
    )
    server.start()

    conn = mysql.connector.connect(
        host="localhost",
        port=server.local_bind_port,
        user=user,
        passwd=password,
        db=database,
        auth_plugin="mysql_native_password",
    )

    df = create_get_dist_pipeline(conn)(
        {"bowler_id": 8058, "batsman_id": 9319, "ground_id": 147, "league_id": 9}
    )

    print(df)

    conn.close()
    server.stop()
