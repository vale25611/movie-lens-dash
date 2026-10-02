"""
MovieLens dashboard — four required charts + a couple of filters.

Genre handling (read this before trusting any genre count):
Movies carry pipe-separated genres (e.g. "Crime|Drama"). A movie is NOT
assigned a single primary genre. For any genre chart we split on "|", then
"explode" so each movie-genre pair is its own row. A film tagged Drama and
Crime is counted once in Drama and once in Crime. Totals across genres will
therefore exceed the number of movies.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).parent / "movie_ratings.csv"

CHART_COLORS = {
    "bar": "#E8C547",
    "bar_low": "#C45C26",
    "line": "#7EB8D4",
    "accent": "#E8C547",
}

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#F4F1EA", size=13),
    margin=dict(l=16, r=16, t=48, b=16),
    title=dict(font=dict(size=16, color="#F4F1EA")),
)


@st.cache_data
def load_ratings() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["genres"] = df["genres"].fillna("unknown")
    return df


@st.cache_data
def unique_movies(ratings: pd.DataFrame) -> pd.DataFrame:
    return ratings.drop_duplicates(subset=["movie_id"]).copy()


def explode_genres(frame: pd.DataFrame) -> pd.DataFrame:
    exploded = frame.assign(genre=frame["genres"].str.split("|")).explode("genre")
    exploded["genre"] = exploded["genre"].str.strip()
    exploded = exploded.dropna(subset=["genre"])
    return exploded[exploded["genre"].str.lower() != "unknown"]


def apply_filters(
    ratings: pd.DataFrame,
    year_min: int,
    year_max: int,
    selected_genres: list[str],
    full_year_span: bool,
) -> pd.DataFrame:
    in_years = (ratings["year"] >= year_min) & (ratings["year"] <= year_max)
    if full_year_span:
        in_years = in_years | ratings["year"].isna()
    filtered = ratings[in_years]
    if selected_genres:
        selected = set(selected_genres)
        mask = filtered["genres"].apply(
            lambda g: bool(selected.intersection(g.split("|")))
        )
        filtered = filtered[mask]
    return filtered


def style_figure(fig: go.Figure, *, height: int = 420) -> go.Figure:
    fig.update_layout(height=height, **PLOT_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(244,241,234,0.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(244,241,234,0.08)", zeroline=False)
    return fig


def genre_breakdown_chart(movies: pd.DataFrame) -> go.Figure:
    exploded = explode_genres(movies)
    counts = (
        exploded.groupby("genre", as_index=False)
        .agg(movies=("movie_id", "nunique"))
        .sort_values("movies", ascending=True)
    )
    fig = px.bar(
        counts,
        x="movies",
        y="genre",
        orientation="h",
        title="Rated movies per genre (a movie can appear in more than one bar)",
        labels={"movies": "Number of distinct movies", "genre": ""},
        color_discrete_sequence=[CHART_COLORS["bar"]],
    )
    fig.update_traces(hovertemplate="%{y}: %{x} movies<extra></extra>")
    return style_figure(fig, height=520)


def genre_satisfaction_chart(ratings: pd.DataFrame) -> tuple[go.Figure, pd.DataFrame]:
    exploded = explode_genres(ratings)
    stats = (
        exploded.groupby("genre", as_index=False)
        .agg(avg_rating=("rating", "mean"), n_ratings=("rating", "size"))
        .sort_values("avg_rating", ascending=True)
    )
    stats["avg_rating"] = stats["avg_rating"].round(3)
    fig = px.bar(
        stats,
        x="avg_rating",
        y="genre",
        orientation="h",
        title="Mean rating by genre (each rating counts toward every tag on that movie)",
        labels={"avg_rating": "Mean rating (1–5)", "genre": ""},
        color="avg_rating",
        color_continuous_scale=["#C45C26", "#E8C547", "#8FBF7A"],
        hover_data={"n_ratings": True, "avg_rating": ":.2f"},
    )
    fig.update_coloraxes(showscale=False)
    return style_figure(fig, height=520), stats


def ratings_over_time_chart(ratings: pd.DataFrame) -> go.Figure:
    yearly = (
        ratings.dropna(subset=["year"])
        .groupby("year", as_index=False)
        .agg(mean_rating=("rating", "mean"), n_ratings=("rating", "size"))
    )
    yearly["year"] = yearly["year"].astype(int)
    fig = px.line(
        yearly,
        x="year",
        y="mean_rating",
        title="Mean rating by movie release year (not the year the rating was submitted)",
        labels={"year": "Release year", "mean_rating": "Mean rating"},
        markers=True,
        color_discrete_sequence=[CHART_COLORS["line"]],
        hover_data={"n_ratings": True, "mean_rating": ":.2f"},
    )
    fig.update_traces(line=dict(width=2))
    fig.update_yaxes(range=[1, 5])
    return style_figure(fig)


def top_movies_chart(ratings: pd.DataFrame, floor: int) -> tuple[go.Figure, pd.DataFrame]:
    stats = ratings.groupby(["movie_id", "title"], as_index=False).agg(
        avg_rating=("rating", "mean"),
        n_ratings=("rating", "size"),
        year=("year", "first"),
    )
    eligible = stats[stats["n_ratings"] >= floor].sort_values(
        ["avg_rating", "n_ratings"], ascending=[False, False]
    )
    top5 = eligible.head(5).copy()
    top5["label"] = top5.apply(
        lambda r: f"{r['title']}"
        + (f" ({int(r['year'])})" if pd.notna(r["year"]) else ""),
        axis=1,
    )
    top5 = top5.sort_values("avg_rating", ascending=True)
    fig = px.bar(
        top5,
        x="avg_rating",
        y="label",
        orientation="h",
        title=f"Top 5 movies with at least {floor} ratings",
        labels={"avg_rating": "Mean rating", "label": ""},
        color_discrete_sequence=[CHART_COLORS["bar"]],
        hover_data={"n_ratings": True, "avg_rating": ":.3f"},
    )
    fig.update_xaxes(range=[0, 5])
    return style_figure(fig, height=360), top5.sort_values(
        "avg_rating", ascending=False
    ).reset_index(drop=True)


def small_top_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["Movie", "Mean", "N"])
    out = frame[["title", "avg_rating", "n_ratings"]].copy()
    out["avg_rating"] = out["avg_rating"].round(3)
    return out.rename(
        columns={"title": "Movie", "avg_rating": "Mean", "n_ratings": "N"}
    ).reset_index(drop=True)


def main() -> None:
    st.set_page_config(
        page_title="MovieLens Dashboard",
        page_icon="🎬",
        layout="wide",
    )

    ratings = load_ratings()
    movies_all = unique_movies(ratings)
    all_genres = sorted(
        explode_genres(movies_all)["genre"].unique().tolist()
    )
    year_lo = int(ratings["year"].min())
    year_hi = int(ratings["year"].max())

    st.title("MovieLens Dashboard")
    st.caption(
        "100,000 ratings from GroupLens. Filters on the left apply to every chart."
    )

    with st.sidebar:
        st.header("Filters")
        year_range = st.slider(
            "Release year range",
            min_value=year_lo,
            max_value=year_hi,
            value=(year_lo, year_hi),
        )
        selected_genres = st.multiselect(
            "Genres (leave empty for all)",
            options=all_genres,
            help="Keeps movies that include at least one of the selected genres.",
        )
        st.divider()
        rating_floor = st.slider(
            "Minimum ratings for the top-movies list",
            min_value=50,
            max_value=150,
            value=50,
            step=10,
            help="Question 4 floor. Drag to 150 to see how the top 5 changes.",
        )

    filtered = apply_filters(
        ratings,
        year_range[0],
        year_range[1],
        selected_genres,
        full_year_span=(year_range[0] == year_lo and year_range[1] == year_hi),
    )
    movies = unique_movies(filtered)

    if filtered.empty:
        st.warning("No ratings match those filters. Widen the year range or genres.")
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ratings shown", f"{len(filtered):,}")
    k2.metric("Movies shown", f"{movies['movie_id'].nunique():,}")
    k3.metric("Mean rating", f"{filtered['rating'].mean():.2f}")
    k4.metric("Release years", f"{year_range[0]}–{year_range[1]}")

    st.subheader("1. Genre breakdown")
    st.write(
        "How genres are distributed among **movies that were rated**. "
        "Counts are unique movies, not ratings. Multi-genre films are counted "
        "once per tag, so the bars add up to more than the movie total. "
        "Two films tagged `unknown` are left out of this chart."
    )
    st.plotly_chart(genre_breakdown_chart(movies), use_container_width=True)

    st.subheader("2. Genre satisfaction")
    st.write(
        "Mean rating by genre, using every individual rating of movies tagged "
        "with that genre (popular films weigh more than obscure ones)."
    )
    fig2, genre_stats = genre_satisfaction_chart(filtered)
    high = genre_stats.iloc[-1]
    low = genre_stats.iloc[0]
    c_high, c_low = st.columns(2)
    c_high.success(
        f"Highest: **{high['genre']}** at {high['avg_rating']:.2f} "
        f"({int(high['n_ratings']):,} ratings)"
    )
    c_low.error(
        f"Lowest: **{low['genre']}** at {low['avg_rating']:.2f} "
        f"({int(low['n_ratings']):,} ratings)"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("3. Ratings over time")
    st.write(
        "Mean rating by **movie release year** (`year`), not the year the "
        "user submitted the rating (`rating_year`). Early decades have far "
        "fewer films, so those points jump around more."
    )
    st.plotly_chart(ratings_over_time_chart(filtered), use_container_width=True)

    st.subheader("4. Best movies, with a floor")
    st.write(
        "Top 5 by mean rating among movies with at least **50** ratings. "
        "Use the sidebar slider to raise that floor to **150** and compare."
    )
    fig4, top5 = top_movies_chart(filtered, rating_floor)
    if top5.empty:
        st.warning(
            f"No movies in this slice have {rating_floor}+ ratings. "
            "Lower the floor or clear some filters."
        )
    else:
        st.plotly_chart(fig4, use_container_width=True)
        display = top5[["title", "year", "avg_rating", "n_ratings"]].copy()
        display["year"] = display["year"].apply(
            lambda y: int(y) if pd.notna(y) else None
        )
        display["avg_rating"] = display["avg_rating"].round(3)
        st.dataframe(
            display.rename(
                columns={
                    "title": "Movie",
                    "year": "Year",
                    "avg_rating": "Mean rating",
                    "n_ratings": "Ratings",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    compare50, compare150 = st.columns(2)
    with compare50:
        st.caption("At a floor of 50")
        _, t50 = top_movies_chart(filtered, 50)
        st.dataframe(small_top_table(t50), hide_index=True, use_container_width=True)
    with compare150:
        st.caption("At a floor of 150")
        _, t150 = top_movies_chart(filtered, 150)
        st.dataframe(small_top_table(t150), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
